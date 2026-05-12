进程记录:
1. 确定 Hermes-Lite 目标
2. 设计模块化框架
3. 定义 Agent / Skill 接口
4. 设计插件注册加载机制
5. 配置驱动 Agent 与 Skill 权限
6. 集成 OllamaSkill 与 MCPSkill
7. 准备 /doc 记录项目目标与思考过程
8. 实现配置驱动插件加载器、运行时注册表与 Agent/Skill 权限绑定
9. 实现 TaskManager、TaskQueue、依赖解析与 FastAPI 任务接口
10. OllamaSkill 切换为 Ollama `/api/chat` 调用格式，并增加健康检查
11. 增加 `/registry`、`/agents`、`/skills`、`/admin/reload` 等运行接口
12. 增加模型适配器与 RAG 向量库适配器，默认适配 `qwen3:14b`
13. 预留 `qwen3-vl:8b`、`bge-m3:latest`、Chroma、Milvus 的可插拔配置
