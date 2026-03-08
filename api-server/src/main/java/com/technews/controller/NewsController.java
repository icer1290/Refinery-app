package com.technews.controller;

import com.technews.dto.response.ApiResponse;
import com.technews.dto.response.NewsArticleResponse;
import com.technews.dto.response.SimilarArticleResponse;
import com.technews.service.AuthService;
import com.technews.service.NewsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/news")
@RequiredArgsConstructor
@Tag(name = "News", description = "News endpoints")
public class NewsController {

    private final NewsService newsService;
    private final AuthService authService;

    @GetMapping("/today")
    @Operation(summary = "Get today's news")
    public ResponseEntity<ApiResponse<List<NewsArticleResponse>>> getTodayNews() {
        List<NewsArticleResponse> news;
        try {
            Long userId = authService.getCurrentUser().getId();
            news = newsService.getTodayNewsWithFavorites(userId);
        } catch (Exception e) {
            news = newsService.getTodayNews();
        }
        return ResponseEntity.ok(ApiResponse.success(news));
    }

    @GetMapping("/archive")
    @Operation(summary = "Get archived news by date range")
    public ResponseEntity<ApiResponse<List<NewsArticleResponse>>> getArchiveNews(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {

        List<NewsArticleResponse> news;
        try {
            Long userId = authService.getCurrentUser().getId();
            news = newsService.getArchiveNewsWithFavorites(startDate, endDate, userId);
        } catch (Exception e) {
            news = newsService.getArchiveNews(startDate, endDate);
        }
        return ResponseEntity.ok(ApiResponse.success(news));
    }

    @GetMapping("/dates")
    @Operation(summary = "Get available dates with news")
    public ResponseEntity<ApiResponse<List<LocalDate>>> getAvailableDates() {
        List<LocalDate> dates = newsService.getAvailableDates();
        return ResponseEntity.ok(ApiResponse.success(dates));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get news by ID")
    public ResponseEntity<ApiResponse<NewsArticleResponse>> getNewsById(@PathVariable UUID id) {
        NewsArticleResponse news;
        try {
            Long userId = authService.getCurrentUser().getId();
            news = newsService.getNewsByIdWithFavorite(id, userId);
        } catch (Exception e) {
            news = newsService.getNewsById(id);
        }
        return ResponseEntity.ok(ApiResponse.success(news));
    }

    @PostMapping("/{id}/favorite")
    @Operation(summary = "Add news to favorites", security = @SecurityRequirement(name = "Bearer"))
    public ResponseEntity<ApiResponse<Void>> addFavorite(@PathVariable UUID id) {
        newsService.addFavorite(id);
        return ResponseEntity.ok(ApiResponse.success("Added to favorites", null));
    }

    @DeleteMapping("/{id}/favorite")
    @Operation(summary = "Remove news from favorites", security = @SecurityRequirement(name = "Bearer"))
    public ResponseEntity<ApiResponse<Void>> removeFavorite(@PathVariable UUID id) {
        newsService.removeFavorite(id);
        return ResponseEntity.ok(ApiResponse.success("Removed from favorites", null));
    }

    @GetMapping("/{id}/similar")
    @Operation(summary = "Find similar articles using vector search")
    public ResponseEntity<ApiResponse<List<SimilarArticleResponse>>> findSimilarArticles(
            @PathVariable UUID id,
            @RequestParam(defaultValue = "5") int limit,
            @RequestParam(defaultValue = "0.7") double threshold) {
        List<SimilarArticleResponse> similarArticles = newsService.findSimilarArticles(id, limit, threshold);
        return ResponseEntity.ok(ApiResponse.success(similarArticles));
    }
}