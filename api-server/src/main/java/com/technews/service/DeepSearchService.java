package com.technews.service;

import com.technews.client.AiEngineClient;
import com.technews.dto.request.DeepSearchRequest;
import com.technews.dto.response.DeepSearchResponse;
import com.technews.exception.ResourceNotFoundException;
import com.technews.repository.NewsArticleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class DeepSearchService {

    private final AiEngineClient aiEngineClient;
    private final NewsArticleRepository newsArticleRepository;

    public DeepSearchResponse executeDeepSearch(UUID articleId, Integer maxIterations) {
        // Validate article exists
        newsArticleRepository.findById(articleId)
                .orElseThrow(() -> new ResourceNotFoundException("NewsArticle", "id", articleId));

        log.info("Executing deep search for article: {} with max iterations: {}", articleId, maxIterations);

        DeepSearchRequest request = DeepSearchRequest.builder()
                .articleId(articleId.toString())
                .maxIterations(maxIterations != null ? maxIterations : 5)
                .build();

        return aiEngineClient.executeDeepSearch(request);
    }
}