import streamlit as st
from llama_index.core.llms import ChatMessage
import logging
import time
from llama_index.llms.ollama import Ollama
import traceback

# 로그 설정 (디버그 레벨로 설정)
logging.basicConfig(level=logging.DEBUG)

# 세션 상태에 채팅 목록이 없으면 초기화
if 'chat_sessions' not in st.session_state:
    st.session_state.chat_sessions = {}  # 각 채팅 세션을 저장
if 'current_chat' not in st.session_state:
    st.session_state.current_chat = None  # 현재 열려있는 채팅 세션
if 'last_displayed_message_index' not in st.session_state:
    st.session_state.last_displayed_message_index = {}  # 각 세션별 마지막 출력된 메시지 인덱스 기록

# 새로운 채팅을 생성하는 함수
def new_chat_session():
    chat_id = len(st.session_state.chat_sessions) + 1  # 새로운 채팅 ID
    session_name = f"채팅 {chat_id}"
    st.session_state.chat_sessions[session_name] = []  # 새로운 채팅 세션 추가
    st.session_state.current_chat = session_name  # 새로운 채팅으로 설정
    st.session_state.last_displayed_message_index[session_name] = 0  # 인덱스 초기화

# 처음에 채팅 세션이 없을 때 첫 번째 채팅 세션을 자동으로 생성
def initialize_first_chat_session():
    if not st.session_state.chat_sessions:  # 세션이 없으면
        new_chat_session()

# 실시간으로 스트리밍 채팅 메시지를 생성하는 함수
def stream_chat(model, messages):
    try:
        llm = Ollama(model=model, request_timeout=120.0)
        resp = llm.stream_chat(messages)
        response = ""

        # 스트리밍 응답을 실시간으로 저장 (단, 최종 결과만 반환)
        for r in resp:
            response += r.delta

        logging.info(f"Model: {model}, Messages: {messages}, Response: {response}")
        return response
    except Exception as e:
        # 에러 로그와 스택 트레이스 출력
        logging.error(f"스트리밍 에러 발생: {str(e)}\n{traceback.format_exc()}")
        raise e

# 메인 함수
def main():
    st.title("LLM 모델과 채팅하기")
    logging.info("앱 시작")

    # 사이드바: LocalLLM 기능 및 기존 채팅 기록 불러오기
    st.sidebar.header("LocalLLM")

    # 모델 선택 (좌측 사이드바 상단)
    available_models = ["llama3.2", "gpt-4", "gpt-3.5", "llama2", "other_model"]
    model = st.sidebar.selectbox("모델을 선택해주세요", available_models)

    # 새로운 채팅 세션을 생성하는 버튼
    if st.sidebar.button("새로운 채팅 시작"):
        new_chat_session()

    # 첫 번째 채팅 세션을 자동으로 생성 (앱 로드 시)
    initialize_first_chat_session()

    # 기존에 저장된 채팅 세션 목록을 좌측에 표시
    chat_options = list(st.session_state.chat_sessions.keys())
    if chat_options:
        selected_chat = st.sidebar.radio("채팅 기록 선택", chat_options, index=chat_options.index(st.session_state.current_chat))
        st.session_state.current_chat = selected_chat  # 선택된 채팅 세션으로 전환

    # 새로운 세션이 만들어지면 현재 세션으로 설정
    if st.session_state.current_chat is None and chat_options:
        st.session_state.current_chat = chat_options[0]

    # 현재 채팅 세션이 선택되었을 때만 작동
    if st.session_state.current_chat:
        chat_session = st.session_state.chat_sessions[st.session_state.current_chat]

        # 마지막으로 출력된 메시지 인덱스 가져오기
        last_index = st.session_state.last_displayed_message_index.get(st.session_state.current_chat, 0)

        # 모든 메시지를 출력 (중복 방지)
        for i, message in enumerate(chat_session):
            if message["role"] == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.write(message["content"], style="color: blue;")  # 사용자 메시지 파란색
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(message["content"], style="color: green;")  # 모델 응답 초록색

        # 마지막 출력 메시지 인덱스 업데이트
        st.session_state.last_displayed_message_index[st.session_state.current_chat] = len(chat_session)

        # 사용자 입력 처리
        if prompt := st.chat_input("질문해주세요"):
            chat_session.append({"role": "user", "content": prompt})
            logging.info(f"유저 인풋: {prompt}")

            # 새로운 메시지만 출력
            with st.chat_message("user", avatar="🧑"):
                st.write(prompt, style="color: blue;")  # 사용자 메시지 파란색

            # 응답을 생성 중인 경우 처리
            with st.chat_message("assistant"):
                start_time = time.time()  # 응답 생성 시작 시간 기록
                logging.info("응답 생성 중...")

            with st.spinner("응답 생성하는 중.."):
                try:
                    # 메시지를 LLM 모델에 맞는 형식으로 변환
                    messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in chat_session]
                    response_message = stream_chat(model, messages)

                    # 응답 시간 계산 및 표시 (한 번만 출력)
                    duration = time.time() - start_time
                    response_message_with_duration = f"{response_message}\n\nDuration: {duration:.2f} seconds"
                    chat_session.append({"role": "assistant", "content": response_message_with_duration})

                    # 새로운 응답만 출력 (중복 방지)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(response_message_with_duration, style="color: green;")

                except Exception as e:
                    # 에러 발생 시 메시지 추가
                    chat_session.append({"role": "assistant", "content": str(e)})
                    logging.error(f"에러 발생: {str(e)}")

        # 메시지 개수가 너무 많으면 초기화 (성능 문제 방지)
        if len(chat_session) > 100:
            st.warning("메시지가 너무 많습니다. 새로운 채팅을 시작해주세요.")
            st.session_state.chat_sessions[st.session_state.current_chat].clear()

# 메인 함수 실행
if __name__ == "__main__":
    main()
