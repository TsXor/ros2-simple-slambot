#include <cmath>
#include <memory>
#include <chrono>
#include <thread>
#include <variant>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2/LinearMath/Matrix3x3.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"

using namespace std::chrono_literals;

class InitialRotationNode : public rclcpp::Node {

  enum class StateType : std::size_t {
    initial,
    wait_nav2,
    small_delay,
    rotate,
    finished
  };
  struct s_initial {};
  struct s_wait_nav2 {
    rclcpp_action::Client<nav2_msgs::action::NavigateToPose>::SharedPtr client;
    s_wait_nav2() {}
  };
  struct s_small_delay {
    int ticks_left;
    s_small_delay(int ticks): ticks_left(ticks) {}
  };
  struct s_rotate {
    rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr cmd_vel_pub;
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub;
    std::optional<double> last_yaw;
    double total_rotated;
    double target_rotation;
    s_rotate(double target_rotation_): total_rotated(0.0), target_rotation(target_rotation_) {}
  };
  struct s_finished {};

  std::variant<
    s_initial,
    s_wait_nav2,
    s_small_delay,
    s_rotate,
    s_finished
  > state_;
  rclcpp::TimerBase::SharedPtr timer_;

  void on_odom(const nav_msgs::msg::Odometry::SharedPtr msg) {
    if (StateType(this->state_.index()) != StateType::rotate)
      return;
    auto& state = std::get<std::size_t(StateType::rotate)>(this->state_);
    tf2::Quaternion quat;
    tf2::fromMsg(msg->pose.pose.orientation, quat);
    tf2::Matrix3x3 mat(quat);
    double roll, pitch, yaw;
    mat.getRPY(roll, pitch, yaw);

    auto last_yaw = state.last_yaw.value_or(0.0);
    double diff = yaw - last_yaw;
    while (diff > M_PI)  diff -= 2.0 * M_PI;
    while (diff < -M_PI) diff += 2.0 * M_PI;
    state.total_rotated += std::abs(diff);
    state.last_yaw = yaw;
  }

  void on_timer() {
    switch (StateType(this->state_.index())) {
      case StateType::initial: {
        auto& new_state = this->state_.emplace<std::size_t(StateType::wait_nav2)>();
        using Nav2Action = nav2_msgs::action::NavigateToPose;
        new_state.client = rclcpp_action::create_client<Nav2Action>(this, "navigate_to_pose");
        RCLCPP_INFO(this->get_logger(), "waiting for nav2 to be ready ...");
      } break;

      case StateType::wait_nav2: {
        auto& state = std::get<std::size_t(StateType::wait_nav2)>(this->state_);
        if (state.client->action_server_is_ready()) {
          this->state_.emplace<std::size_t(StateType::small_delay)>(20);
          RCLCPP_INFO(this->get_logger(), "nav2 is ready, begin rotating after a small delay");
        }
      } break;

      case StateType::small_delay: {
        auto& state = std::get<std::size_t(StateType::small_delay)>(this->state_);
        state.ticks_left -= 1;
        if (state.ticks_left <= 0) {
          double target_rotation = this->get_parameter("target_rotation").as_double();
          auto& new_state = this->state_.emplace<std::size_t(StateType::rotate)>(target_rotation);
          std::string cmd_vel_topic = this->get_parameter("cmd_vel_topic").as_string();
          std::string odom_topic    = this->get_parameter("odom_topic").as_string();
          using geometry_msgs::msg::TwistStamped;
          using nav_msgs::msg::Odometry;
          auto on_odom = [this](Odometry::SharedPtr msg) -> void { this->on_odom(msg); };
          new_state.cmd_vel_pub = this->create_publisher<TwistStamped>(cmd_vel_topic, 10);
          new_state.odom_sub = this->create_subscription<Odometry>(odom_topic, 10, std::move(on_odom));
        }
      } break;

      case StateType::rotate: {
        auto& state = std::get<std::size_t(StateType::rotate)>(this->state_);
        double rotation_speed = this->get_parameter("rotation_speed").as_double();
        if (state.last_yaw.has_value()) {
          geometry_msgs::msg::Twist cmd;
          if (state.total_rotated < state.target_rotation) {
            geometry_msgs::msg::TwistStamped cmd;
            cmd.twist.angular.z = rotation_speed;
            state.cmd_vel_pub->publish(cmd);
          } else {
            RCLCPP_INFO(this->get_logger(), "initial exploration finished, quitting");
            this->state_.emplace<std::size_t(StateType::finished)>();
          }
        }
      } break;

      case StateType::finished: {
        this->timer_->cancel();
        rclcpp::shutdown();
      } break;
    }
  }

public:
  InitialRotationNode() : Node("initial_exploration") {
    this->declare_parameter("rotation_speed", 0.5 /* rad/s */);
    this->declare_parameter("target_rotation", 2.0 * M_PI);
    this->declare_parameter("cmd_vel_topic", "cmd_vel");
    this->declare_parameter("odom_topic", "odom");

    timer_ = this->create_wall_timer(50ms, [this]() { this->on_timer(); });
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<InitialRotationNode>());
  rclcpp::shutdown();
  return 0;
}
