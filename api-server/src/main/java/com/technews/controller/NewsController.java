package com.technews.controller;

import com.technews.dto.response.ApiResponse;
import com.technews.dto.response.NewsResponse;
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

@RestController
@RequestMapping("/api/news")
@RequiredArgsConstructor
@Tag(name = "News", description = "News endpoints")
public class NewsController {

    private final NewsService newsService;
    private final AuthService authService;

    @GetMapping("/today")
    @Operation(summary = "Get today's news")
    public ResponseEntity<ApiResponse<List<NewsResponse>>> getTodayNews() {
        List<NewsResponse> news;
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
    public ResponseEntity<ApiResponse<List<NewsResponse>>> getArchiveNews(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {

        List<NewsResponse> news;
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
    public ResponseEntity<ApiResponse<NewsResponse>> getNewsById(@PathVariable Long id) {
        NewsResponse news;
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
    public ResponseEntity<ApiResponse<Void>> addFavorite(@PathVariable Long id) {
        newsService.addFavorite(id);
        return ResponseEntity.ok(ApiResponse.success("Added to favorites", null));
    }

    @DeleteMapping("/{id}/favorite")
    @Operation(summary = "Remove news from favorites", security = @SecurityRequirement(name = "Bearer"))
    public ResponseEntity<ApiResponse<Void>> removeFavorite(@PathVariable Long id) {
        newsService.removeFavorite(id);
        return ResponseEntity.ok(ApiResponse.success("Removed from favorites", null));
    }
}
