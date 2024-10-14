import streamlit as st
from llama_index.core.llms import ChatMessage
import logging
import time
from llama_index.llms.ollama import Ollama

logging.basicConfig(level=logging.INFO)

if 'messages' not in st.session_state:
        st.session_state.messages = []

def stream_chat(model, messages):
      try:
            llm = Ollama(model=model, request_timeout=120.0)
            resp = llm.stream_chat(messages)
            response = ""
            response_placeholder = st.empty()

            for r in resp:
                  response += r.delta
                  response_placeholder.write(response)
            logging.info(f"Model: {model}, Messages: {messages}, Response: {response}")
            return response
      except Exception as e:
            logging.error(f"스트리밍 에러 발생: {str(e)}")
            raise e

def main():
      st.title("LLM 모델과 채팅하기")
      logging.info("앱 시작")

      model = st.sidebar.selectbox("모델을 선택해주세요", ["llama3.2"])
      logging.info(f"선택한 모델: {model}")

      if prompt := st.chat_input("질문해주세요"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            logging.info(f"유저 인풋: {prompt}")

            for message in st.session_state.messages:
                  with st.chat_message(message["role"]):
                        st.write(message["content"])

            if st.session_state.messages[-1]["role"] != "assistant":
                  with st.chat_message("assistant"):
                    start_time = time.time()
                    logging.info("응답 생성중")

            with st.spinner("응답 생성하는 중.."):
                try:
                      messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in st.session_state.messages]
                      response_message = stream_chat(model, messages)
                      duration = time.time() - start_time
                      respone_message_with_duration = f"{response_message}\n\nDuration: {duration:.2f} seconds"
                      st.session_state.messages.append({"role": "assistant", "content": respone_message_with_duration})
                      st.write(f"응답 시간: {duration:.2f} 초")               
                
                except Exception as e:
                      st.session_state.messasges.append({"role": "assistant", "content": str(e)})
                      logging.error(f"에러 발생: {str(e)}")

if __name__ == "__main__":
    main()