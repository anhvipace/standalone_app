# Try to import langchain components
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not available. Agent features will be limited.")

from analysis_tools import load_las_file, run_analysis, reconstruct_and_save_3d_mesh

def create_agent_executor():
    if not LANGCHAIN_AVAILABLE:
        # Return a simple fallback executor
        class SimpleExecutor:
            def invoke(self, inputs):
                return {"output": "LangChain not available. Please use standalone_app.py for full functionality."}
        return SimpleExecutor()
    
    # Sử dụng model ổn định nhất từ danh sách của bạn
    llm = ChatGoogleGenerativeAI(model="models/gemini-pro-latest", temperature=0)

    tools = [load_las_file, run_analysis, reconstruct_and_save_3d_mesh]

    # Prompt được viết lại để nghiêm ngặt hơn
    prompt_template = """
Bạn là một trợ lý kỹ thuật, nhiệm vụ của bạn là hoàn thành mục tiêu của người dùng.
Bạn phải suy nghĩ từng bước và chỉ sử dụng các công cụ được cung cấp.

**QUY TẮC TUYỆT ĐỐI:**
1.  Sau mỗi lần "Suy nghĩ:", bạn BẮT BUỘC phải viết "Hành động:".
2.  "Hành động:" phải là một trong các tên công cụ sau: [{tool_names}].
3.  Nếu một bước thất bại, hãy dừng lại và báo cáo lỗi trong câu trả lời cuối cùng.

**ĐỊNH DẠNG BẮT BUỘC:**

Mục tiêu: mục tiêu bạn phải hoàn thành
Suy nghĩ: (viết suy nghĩ của bạn ở đây)
Hành động: (viết tên một công cụ ở đây)
Đầu vào hành động: (viết đầu vào cho công cụ đó)
Quan sát: (đây là kết quả của công cụ)
(lặp lại chu trình Suy nghĩ/Hành động/Đầu vào/Quan sát)
Suy nghĩ: Tôi đã hoàn thành mục tiêu.
Câu trả lời cuối cùng: (viết câu trả lời cuối cùng cho người dùng ở đây)

BẮT ĐẦU!

Mục tiêu: {input}
Suy nghĩ:{agent_scratchpad}
"""
    prompt = PromptTemplate.from_template(prompt_template)

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True, # Tự động sửa lỗi định dạng
        max_iterations=30 # Cho phép nhiều bước hơn
    )
    
    return agent_executor