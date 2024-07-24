from agent import Agent
import streamlit as st


def main():
    st.title("search smart")
    
    if "agent" not in st.session_state:
        st.session_state.agent = Agent(system_prompt=open("system_prompt.txt", 'r').read())

    if "history" not in st.session_state:
        st.session_state.history = []
    
    for history in st.session_state.history:
        with st.chat_message(history["role"]):
            st.markdown(history["text"])
    
    if prompt := st.chat_input("Enter your message..."):
        st.session_state.history.append({"role": "user", "text": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            response, sources = st.session_state.agent.send_message(prompt)
            if sources:
                st.write(sources)
            message_placeholder.markdown(response)
        st.session_state.history.append({"role": "assistant", "text": response})
        
if __name__ == '__main__':
    main()