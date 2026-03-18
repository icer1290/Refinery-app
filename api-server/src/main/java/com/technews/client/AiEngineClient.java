package com.technews.client;

import com.technews.dto.request.DeepGraphRequest;
import com.technews.dto.request.DeepSearchRequest;
import com.technews.dto.response.DeepGraphResponse;
import com.technews.dto.response.DeepSearchResponse;
import com.technews.exception.AiEngineException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

@Slf4j
@Component
@RequiredArgsConstructor
public class AiEngineClient {

    private final WebClient.Builder webClientBuilder;

    @Value("${ai-engine.base-url}")
    private String baseUrl;

    @Value("${ai-engine.deepsearch.path}")
    private String deepSearchPath;

    @Value("${ai-engine.deepsearch.timeout}")
    private int timeout;

    @Value("${ai-engine.deepgraph.path}")
    private String deepGraphPath;

    @Value("${ai-engine.deepgraph.timeout}")
    private int deepGraphTimeout;

    public DeepSearchResponse executeDeepSearch(DeepSearchRequest request) {
        log.info("Calling AI Engine deep search for article: {}", request.getArticleId());

        try {
            // Build request body in snake_case format for Python API
            DeepSearchApiRequest apiRequest = new DeepSearchApiRequest(
                    request.getArticleId(),
                    request.getMaxIterations()
            );

            DeepSearchResponse response = webClientBuilder.build()
                    .post()
                    .uri(baseUrl + deepSearchPath)
                    .bodyValue(apiRequest)
                    .retrieve()
                    .bodyToMono(DeepSearchResponse.class)
                    .block();

            log.info("Deep search completed for article: {}", request.getArticleId());
            return response;

        } catch (WebClientResponseException e) {
            log.error("AI Engine returned error: {} - {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new AiEngineException(mapAiEngineErrorMessage(e), e);
        } catch (Exception e) {
            log.error("Failed to call AI Engine: {}", e.getMessage());
            throw new AiEngineException("DeepSearch 服务暂时不可用，请稍后再试", e);
        }
    }

    private String mapAiEngineErrorMessage(WebClientResponseException e) {
        String responseBody = e.getResponseBodyAsString();

        if (e.getStatusCode().value() == 401 && responseBody.contains("invalid_api_key")) {
            return "DeepSearch 服务密钥无效，请检查 OPENAI_API_KEY 配置";
        }

        if (e.getStatusCode().value() == 401) {
            return "DeepSearch 服务鉴权失败，请检查模型服务配置";
        }

        return "DeepSearch 服务请求失败：" + e.getStatusCode();
    }

    // Inner class for snake_case request format
    private record DeepSearchApiRequest(String article_id, Integer max_iterations) {}

    public DeepGraphResponse executeDeepGraph(DeepGraphRequest request, Long userId) {
        log.info("Calling AI Engine deep graph for {} articles", request.getArticleIds().size());

        try {
            DeepGraphApiRequest apiRequest = new DeepGraphApiRequest(
                    userId,
                    request.getArticleIds(),
                    request.getMaxHops(),
                    request.getExpansionLimit()
            );

            DeepGraphResponse response = webClientBuilder.build()
                    .post()
                    .uri(baseUrl + deepGraphPath)
                    .bodyValue(apiRequest)
                    .retrieve()
                    .bodyToMono(DeepGraphResponse.class)
                    .block();

            log.info("Deep graph analysis completed for {} articles", request.getArticleIds().size());
            return response;

        } catch (WebClientResponseException e) {
            log.error("AI Engine returned error: {} - {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new AiEngineException(mapDeepGraphErrorMessage(e), e);
        } catch (Exception e) {
            log.error("Failed to call AI Engine: {}", e.getMessage());
            throw new AiEngineException("DeepGraph 服务暂时不可用，请稍后再试", e);
        }
    }

    private String mapDeepGraphErrorMessage(WebClientResponseException e) {
        String responseBody = e.getResponseBodyAsString();

        if (e.getStatusCode().value() == 401 && responseBody.contains("invalid_api_key")) {
            return "DeepGraph 服务密钥无效，请检查 OPENAI_API_KEY 配置";
        }

        if (e.getStatusCode().value() == 401) {
            return "DeepGraph 服务鉴权失败，请检查模型服务配置";
        }

        return "DeepGraph 服务请求失败：" + e.getStatusCode();
    }

    // Inner class for snake_case request format
    private record DeepGraphApiRequest(Long user_id, java.util.List<String> article_ids, Integer max_hops, Integer expansion_limit) {}
}
