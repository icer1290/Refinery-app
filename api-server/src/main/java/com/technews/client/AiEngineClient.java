package com.technews.client;

import com.technews.dto.request.DeepSearchRequest;
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
            throw new AiEngineException("AI Engine request failed: " + e.getStatusCode(), e);
        } catch (Exception e) {
            log.error("Failed to call AI Engine: {}", e.getMessage());
            throw new AiEngineException("Failed to connect to AI Engine", e);
        }
    }

    // Inner class for snake_case request format
    private record DeepSearchApiRequest(String article_id, Integer max_iterations) {}
}