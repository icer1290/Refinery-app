package com.technews.service;

import com.technews.client.AiEngineClient;
import com.technews.dto.request.DeepGraphRequest;
import com.technews.dto.response.DeepGraphAnalysisListResponse;
import com.technews.dto.response.DeepGraphAnalysisResponse;
import com.technews.dto.response.DeepGraphResponse;
import com.technews.entity.DeepGraphAnalysis;
import com.technews.entity.User;
import com.technews.exception.ResourceNotFoundException;
import com.technews.repository.DeepGraphAnalysisRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class DeepGraphService {

    private final AiEngineClient aiEngineClient;
    private final AuthService authService;
    private final DeepGraphAnalysisRepository analysisRepository;

    public DeepGraphAnalysisResponse executeAnalysis(DeepGraphRequest request) {
        User user = authService.getCurrentUser();
        log.info("Executing DeepGraph analysis for user {} with {} articles", user.getId(), request.getArticleIds().size());

        DeepGraphResponse response = aiEngineClient.executeDeepGraph(request, user.getId());

        // Response is stored by ai-engine, we need to fetch it from database
        // For now, return the response directly (the ai-engine stores it)
        return DeepGraphAnalysisResponse.builder()
                .userId(user.getId())
                .articleIds(request.getArticleIds().stream().map(UUID::fromString).toList())
                .report(response.getReport())
                .visualizationData(response.getVisualizationData() != null ?
                        convertVisualizationDataToMap(response.getVisualizationData()) : null)
                .maxHops(request.getMaxHops())
                .expansionLimit(request.getExpansionLimit())
                .build();
    }

    public DeepGraphAnalysisListResponse getUserAnalyses(int page, int pageSize) {
        User user = authService.getCurrentUser();
        log.info("Fetching DeepGraph analyses for user {}, page {}, pageSize {}", user.getId(), page, pageSize);

        Page<DeepGraphAnalysis> analyses = analysisRepository
                .findByUserIdOrderByCreatedAtDesc(user.getId(), PageRequest.of(page - 1, pageSize));

        return DeepGraphAnalysisListResponse.builder()
                .analyses(analyses.getContent().stream().map(this::toResponse).toList())
                .total(analyses.getTotalElements())
                .page(page)
                .pageSize(pageSize)
                .build();
    }

    public DeepGraphAnalysisResponse getAnalysis(UUID id) {
        User user = authService.getCurrentUser();
        log.info("Fetching DeepGraph analysis {} for user {}", id, user.getId());

        DeepGraphAnalysis analysis = analysisRepository.findByIdAndUserId(id, user.getId())
                .orElseThrow(() -> new ResourceNotFoundException("DeepGraphAnalysis", "id", id));

        return toResponse(analysis);
    }

    private DeepGraphAnalysisResponse toResponse(DeepGraphAnalysis a) {
        return DeepGraphAnalysisResponse.builder()
                .id(a.getId())
                .userId(a.getUserId())
                .articleIds(a.getArticleIds())
                .report(a.getReport())
                .visualizationData(a.getVisualizationData())
                .maxHops(a.getMaxHops())
                .expansionLimit(a.getExpansionLimit())
                .createdAt(a.getCreatedAt())
                .build();
    }

    private java.util.Map<String, Object> convertVisualizationDataToMap(DeepGraphResponse.VisualizationData data) {
        java.util.Map<String, Object> result = new java.util.HashMap<>();
        result.put("nodes", data.getNodes());
        result.put("edges", data.getEdges());
        result.put("communities", data.getCommunities());
        result.put("stats", data.getStats());
        return result;
    }
}