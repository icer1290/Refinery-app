package com.technews.controller;

import com.technews.dto.request.DeepGraphRequest;
import com.technews.dto.response.ApiResponse;
import com.technews.dto.response.DeepGraphAnalysisListResponse;
import com.technews.dto.response.DeepGraphAnalysisResponse;
import com.technews.service.DeepGraphService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/deepgraph")
@RequiredArgsConstructor
@Tag(name = "DeepGraph", description = "DeepGraph analysis endpoints")
public class DeepGraphController {

    private final DeepGraphService deepGraphService;

    @PostMapping
    @Operation(
            summary = "Execute DeepGraph analysis",
            description = "Performs a comprehensive knowledge graph analysis on selected articles",
            security = @SecurityRequirement(name = "Bearer")
    )
    public ResponseEntity<ApiResponse<DeepGraphAnalysisResponse>> executeAnalysis(
            @Valid @RequestBody DeepGraphRequest request) {
        DeepGraphAnalysisResponse response = deepGraphService.executeAnalysis(request);
        return ResponseEntity.ok(ApiResponse.success("Analysis completed", response));
    }

    @GetMapping
    @Operation(
            summary = "List user's analyses",
            description = "Returns a paginated list of the user's DeepGraph analyses",
            security = @SecurityRequirement(name = "Bearer")
    )
    public ResponseEntity<ApiResponse<DeepGraphAnalysisListResponse>> listAnalyses(
            @Parameter(description = "Page number (1-based)")
            @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "Page size")
            @RequestParam(defaultValue = "20") int pageSize) {
        DeepGraphAnalysisListResponse response = deepGraphService.getUserAnalyses(page, pageSize);
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @GetMapping("/{id}")
    @Operation(
            summary = "Get specific analysis",
            description = "Returns a specific DeepGraph analysis by ID",
            security = @SecurityRequirement(name = "Bearer")
    )
    public ResponseEntity<ApiResponse<DeepGraphAnalysisResponse>> getAnalysis(
            @Parameter(description = "Analysis UUID") @PathVariable UUID id) {
        DeepGraphAnalysisResponse response = deepGraphService.getAnalysis(id);
        return ResponseEntity.ok(ApiResponse.success(response));
    }
}