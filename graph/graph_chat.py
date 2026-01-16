import uuid

from langchain_core.messages import AIMessage
from langgraph.constants import END, START
from langgraph.graph import StateGraph, MessagesState
from langgraph.types import Command

from graph.all_agent import supervisor_agent, research_agent, flight_booking_agent, hotel_booking_agent, \
    car_rental_booking_agent, excursion_booking_agent, memory
from graph.draw_png import draw_graph
from graph.info_node import get_user_info
from graph.my_print import pretty_print_messages

graph = (
    StateGraph(MessagesState)
    .add_node('fetch_user_info', get_user_info)
    .add_node(supervisor_agent,
              destinations=("research_agent", 'flight_booking_agent', 'hotel_booking_agent', 'car_rental_booking_agent',
                            'excursion_booking_agent', END)
              )
    .add_node(research_agent, destinations=(END,))
    .add_node(flight_booking_agent, destinations=(END,))
    .add_node(hotel_booking_agent, destinations=(END,))
    .add_node(car_rental_booking_agent, destinations=(END,))
    .add_node(excursion_booking_agent, destinations=(END,))
    .add_edge(START, 'fetch_user_info')
    .add_edge('fetch_user_info', 'supervisor')
    .compile(checkpointer=memory)
)

# draw_graph(graph, 'graph_supervisor.png')

session_id = str(uuid.uuid4())
# update_dates()  # 每次测试的时候：保证数据库是全新的，保证，时间也是最近的时间

# 配置参数，包含乘客ID和线程ID
config = {
    "configurable": {
        # passenger_id用于我们的航班工具，以获取用户的航班信息
        "passenger_id": "3442 587242",
        # 检查点由session_id访问
        "thread_id": session_id,
    }
}


def execute_graph(user_input: str, session_config: dict = None, verbose: bool = False) -> str:
    """ 执行工作流的函数"""
    if session_config is None:
        session_config = config
    
    result = ''  # AI助手的最后一条消息
    current_state = graph.get_state(session_config)
    if current_state.next:  # 出现了工作流的中断
        human_command = Command(resume={'answer': user_input})
        for chunk in graph.stream(human_command, session_config, stream_mode='values'):
            if verbose:
                pretty_print_messages(chunk, last_message=True)
    else:
        for chunk in graph.stream({'messages': ('user', user_input)}, session_config):
            if verbose:
                pretty_print_messages(chunk, last_message=True)

    # 获取最终状态并提取AI的最后一条消息
    current_state = graph.get_state(session_config)
    if current_state.next:  # 出现了工作流的中断
        result = current_state.interrupts[0].value
    else:
        # 从消息中提取最后一条AI消息
        if current_state.values and 'messages' in current_state.values:
            messages = current_state.values['messages']
            # 从后往前查找最后一条AI消息
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    result = msg.content
                    break
                # 兼容其他消息格式
                elif hasattr(msg, 'content') and hasattr(msg, 'type'):
                    if msg.type == 'ai':
                        result = msg.content
                        break

    return result


# 执行工作流（仅在直接运行此文件时执行）
if __name__ == '__main__':
    while True:
        user_input = input('用户：')
        res = execute_graph(user_input)
        if res:
            print('AI: ', res)
