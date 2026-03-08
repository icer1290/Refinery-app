package com.technews.controller;

import com.technews.dto.response.ApiResponse;
import com.technews.dto.response.DeepSearchResponse;
import com.technews.service.DeepSearchService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/news")
@RequiredArgsConstructor
@Tag(name = "DeepSearch", description = "Deep search analysis endpoints")
public class DeepSearchController {

    private final DeepSearchService deepSearchService;

    @PostMapping("/{id}/deepsearch")
    @Operation(
            summary = "Execute deep search analysis on an article",
            description = "Performs a comprehensive deep search analysis using AI to gather additional information about the article topic",
            security = @SecurityRequirement(name = "Bearer")
    )
    public ResponseEntity<ApiResponse<DeepSearchResponse>> executeDeepSearch(
            @Parameter(description = "Article UUID") @PathVariable UUID id,
            @Parameter(description = "Maximum number of search iterations (1-10)")
            @RequestParam(defaultValue = "5") Integer maxIterations) {

        DeepSearchResponse response = deepSearchService.executeDeepSearch(id, maxIterations);
        return ResponseEntity.ok(ApiResponse.success(response));
    }
}