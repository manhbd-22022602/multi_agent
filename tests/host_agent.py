import asyncio
from agents.master.core_graph import graph_router

async def test_host_agent():
    # TEST 1: Forced routing to 'dev'
    # out1 = await graph_router("Tôi muốn biết tiến độ phát triển phần mềm", target_agent="dev")
    # print("\n[TEST 1] Forced route to 'dev':\n", out1)

    # TEST 2: No forced route → Host dùng LLM để phân loại (nội dung thiên về QA)
    # out2 = await graph_router("Tôi gặp lỗi khi đăng nhập, hãy kiểm tra giúp tôi", target_agent=None)
    # print("\n[TEST 2] LLM chọn agent phù hợp:\n", out2)

    # TEST 3: Nội dung không rõ ràng → Host tự trả lời
    out3 = await graph_router("Cảm ơn bạn nha", target_agent=None)
    print("\n[TEST 3] Host tự trả lời vì không phân loại được:\n", out3)

if __name__ == "__main__":
    asyncio.run(test_host_agent())
