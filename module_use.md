除了在Dify应用开发平台中使用模型推理接入点，也可在业务系统中直接调用模型推理接入点，使用大模型能力快速扩展业务
域名
暂时无法在飞书文档外展示此内容
鉴权
所有 API 请求都应在 Authorization HTTP Header 中包含您的 API-Key, API_KEY是在你在AI开发者平台上申请的API KEY
  Authorization: Bearer {API_KEY}
Route 路由
/llm
接口说明
暂时无法在飞书文档外展示此内容
模型列表查询
curl https://ai-dev-gateway.zkh360.com/llm/v1/models \  -H "Content-Type: application/json" \  -H "Authorization: Bearer $API_KEY"
对话模型调用
Curl调用示例
文本输入
curl https://ai-dev-gateway.zkh360.com/llm/v1/chat/completions \  -H "Content-Type: application/json" \  -H "Authorization: Bearer $API_KEY" \  -d '{    "model": "ep-20250429102651-hd5dd",    "messages": [      {"role": "system","content": "你是人工智能助手."},      {"role": "user","content": "你好"}    ]  }'
说明： $API_KEY: 是在平台上申请的API KEY, model: 是在线推理接入点ID 其他模型参数参考调用模型详情的参数列表
暂时无法在飞书文档外展示此内容
图像输入
图片URL方式
curl -X POST  https://ai-dev-gateway.zkh360.com/llm/v1/chat/completions \-H "Authorization: Bearer $API_KEY" \-H 'Content-Type: application/json' \-d '{  "model": "ep-20250429102651-hd5dd",  "messages": [{      "role": "user",      "content": [       {"type": "image_url","image_url": {"url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"}},       {"type": "text","text": "这是什么"}       ]}]}'
图片base64编码方式
curl -X POST  https://ai-dev-gateway.zkh360.com/llm/v1/chat/completions \-H "Authorization: Bearer $API_KEY" \-H 'Content-Type: application/json' \-d '{    "model": "ep-20250429102651-hd5dd",    "messages": [        {            "role": "user",            "content": [                {                    "type": "image_url",                    "image_url": {                        "detail": "high",                        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAApQAAAIkCAYAAACgBbtJAAAKq2lDQ1BJQ0MgUHJvZmlsZQAASImVlwdQU+kWgP9700NCS4h0Qg1FkE4AKSG0AArSQVRCEiCUEAJBxY4sruBaUBHBBrpKUXBVi=="                    }                },                {                    "type": "text",                    "text": "这是什么"                }            ]        }    ]}'
工具调用
curl -X POST https://ai-dev-gateway.zkh360.com/llm/v1/chat/completions \-H "Authorization: Bearer $API_KEY" \-H "Content-Type: application/json" \-d '{    "model": "ep-20250429102651-hd5dd",    "messages": [        {            "role": "system",            "content": "You are a helpful assistant."        },        {            "role": "user",             "content": "杭州天气怎么样"        }    ],    "tools": [    {        "type": "function",        "function": {            "name": "get_current_time",            "description": "当你想知道现在的时间时非常有用。",            "parameters": {}        }    },    {        "type": "function",        "function": {            "name": "get_current_weather",            "description": "当你想查询指定城市的天气时非常有用。",            "parameters": {                "type": "object",                "properties": {                    "location":{                        "type": "string",                        "description": "城市或县区，比如北京市、杭州市、余杭区等。"                    }                },                "required": ["location"]            }        }    }  ]}'
Sping AI调用示例
1. pom.xml引入
<dependency>    <groupId>org.springframework.ai</groupId>    <artifactId>spring-ai-starter-model-openai</artifactId>    <version>1.0.0</version></dependency>
2. application.yml配置
spring:  ai:    openai:      api-key: $API_KEY    # API密钥配置      base-url: https://ai-dev-gateway.zkh360.com/llm      chat:        options:          model: ep_20250522_y93v     # 推理接入点ID        completions-path: /v1/chat/completions
说明： $API_KEY: 是在平台上申请的API KEY, model: 是在线推理接入点ID
3. 代码示例
@RestController@RequestMapping("/openai/chat-client")public class OpenAiChatClientController {        private static final String DEFAULT_PROMPT = "你好，介绍下你自己！";        private final ChatClient openAiChatClient;        private final ChatModel chatModel;        public OpenAiChatClientController(ChatModel chatModel) {                this.chatModel = chatModel;                // 构造时，可以设置 ChatClient 的参数                // {@link org.springframework.ai.chat.client.ChatClient};                this.openAiChatClient = ChatClient.builder(chatModel)                                // 实现 Chat Memory 的 Advisor                                // 在使用 Chat Memory 时，需要指定对话 ID，以便 Spring AI 处理上下文。                                .defaultAdvisors(                                                MessageChatMemoryAdvisor.builder(MessageWindowChatMemory.builder().build()).build()                                )                                // 实现 Logger 的 Advisor                                .defaultAdvisors(                                                new SimpleLoggerAdvisor()                                )                                // 设置 ChatClient 中 ChatModel 的 Options 参数                                .defaultOptions(                                                OpenAiChatOptions.builder()                                                                .topP(0.7)                                                                .build()                                )                                .build();        }        // 也可以使用如下的方式注入 ChatClient        // public OpenAIChatClientController(ChatClient.Builder chatClientBuilder) {        //        //          this.openAiChatClient = chatClientBuilder.build();        // }        /**         * ChatClient 简单调用         */        @GetMapping("/simple/chat")        public String simpleChat() {                return openAiChatClient.prompt(DEFAULT_PROMPT).call().content();        }        /**         * ChatClient 流式调用         */        @GetMapping("/stream/chat")        public Flux<String> streamChat(HttpServletResponse response) {                response.setCharacterEncoding("UTF-8");                return openAiChatClient.prompt(DEFAULT_PROMPT).stream().content();        }        /**         * ChatClient 流式响应         */        @GetMapping(value = "/stream/response", produces = MediaType.TEXT_EVENT_STREAM_VALUE)        public Flux<ServerSentEvent<String>> simpleChat(@RequestParam String message) {                return openAiChatClient.prompt()                                .user(message)                                .stream()                                .content()                                .map(content -> ServerSentEvent.<String>builder()                                                .data(content)                                                .build());        }}
向量模型调用
Curl调用示例
curl https://ai-dev-gateway.zkh360.com/llm/v1/embeddings \  -H "Content-Type: application/json" \  -H "Authorization: Bearer $API_KEY" \  -d '{    "model": "ep-20250429102651-hd5dd",    "input": "1: 集团简介-正中集团 - 正中集团创立于2003年，是一家以不动产、科创、投资为核心战略赛道的多元化集团。"  }'
暂时无法在飞书文档外展示此内容
文档模型调用
大模型对话受到模型上下文长度的现状，Qwen-Long提供长达1,000万Token（约1,500万字）的上下文长度，支持上传文档并基于文档进行问答，可以用于快速分析代码、网页、论文、报告、合同、书籍、规范手册、技术文档等 支持的模型有：
1. qwen-long
2. qwen-long-latest
上传文档
curl --location --request POST 'https://ai-dev-gateway.zkh360.com/llm/v1/files' \  --header "Authorization: Bearer $ZKH_API_KEY" \  --form 'file=@"阿里云百炼系列手机产品介绍.docx"' \  --form 'purpose="file-extract"'
参数：
1. file： 文件
2. purpose： 文件用途，默认为file-extract
查询文档列表
curl -X GET https://ai-dev-gateway.zkh360.com/llm/v1/files \-H "Authorization: Bearer $ZKH_API_KEY"
参数：
1. limit ： 数量，默认20
2. purpose： 文件用途，默认为file-extract
返回结果：
{    "id": "file-fe-192efdab8c164ff6aad41bc6",    "bytes": 2865684,    "filename": "temp5256148024703411441.pdf",    "object": "file",    "purpose": "file-extract"}
删除文档
curl -X  DELETE https://ai-dev-gateway.zkh360.com/llm/v1/files/file-fe-192xxxxxx \-H "Authorization: Bearer $ZKH_API_KEY"
基于文档ID调用模型
curl --location 'https://ai-dev-gateway.zkh360.com/llm/v1/chat/completions' \--header "Authorization: Bearer $ZKH_API_KEY" \--header "Content-Type: application/json" \--data '{    "model": "ep-20250429102651-hd5dd",    "messages": [        {"role": "system","content": "You are a helpful assistant."},        {"role": "system","content": "fileid://file-fe-xxx1"},        {"role": "system","content": "fileid://file-fe-xxx2"},        {"role": "user","content": "这两篇文章讲了什么？"}    ],    "stream": true,    "stream_options": {        "include_usage": true    }}'
文档放在system消息中，前缀：fileid://+文档ID，多个可以采用多个system或一个system消息中逗号分隔
{"role": "system","content": "fileid://file-fe-xxx1,fileid://file-fe-xxx2"}
限制说明
1. 文件格式支持文本文件（ TXT、DOCX、PDF、XLSX、EPUB、MOBI、MD、CSV），图片文件（BMP、PNG、JPG/JPEG、GIF 以及PDF扫描件）。图片格式文件大小限制为20M，其他格式文件大小限制为 150MB。单个阿里云账号最多可上传 1 万个文件，总文件大小不得超过 100GB。
2. 请避免直接将文档内容放在role为user的message中，用于role-play的system和user的message限制输入最长为9,000 Token（连续多条user message视为一条user message且长度限制在9,000 Token内）。通过 文件ID 传入文档信息，并在 system 消息中使用返回的 文件ID 时，content 的最大输入限制可扩展至 10,000,000 Token，但 文件ID 的数量限制为不超过 100 个。此外，文件的传入顺序将直接影响模型返回结果的顺序。
Responses API
Responses API 优势
1. 内置工具：内置联网搜索、网页抓取和代码解释器等工具
2. 更灵活的输入：支持直接传入字符串作为模型输入，也兼容 Chat 格式的消息数组。
3. 简化上下文管理：通过传递上一轮响应的 previous_response_id，无需手动构建完整的消息历史数组
curl --location --request POST '/v1/responses' \--header 'Authorization: Bearer {{YOUR_API_KEY}}' \--header 'Content-Type: application/json' \--data-raw '{    "model": "gpt-4.1",    "input": [        {            "role": "user",            "content": "Write a one-sentence bedtime story about a unicorn."        }    ]  }'
具体模型是否支持Responses API，请查看模型详情