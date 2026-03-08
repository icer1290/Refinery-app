package com.technews.controller;

import com.technews.dto.request.UserPreferenceRequest;
import com.technews.dto.response.ApiResponse;
import com.technews.dto.response.NewsArticleResponse;
import com.technews.dto.response.UserPreferenceResponse;
import com.technews.service.NewsService;
import com.technews.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
@Tag(name = "User", description = "User profile and preferences")
public class UserController {

    private final UserService userService;
    private final NewsService newsService;

    @GetMapping("/preferences")
    @Operation(summary = "Get user preferences", security = @SecurityRequirement(name = "Bearer"))
    public ResponseEntity<ApiResponse<UserPreferenceResponse>> getPreferences() {
        UserPreferenceResponse preferences = userService.getUserPreferences();
        return ResponseEntity.ok(ApiResponse.success(preferences));
    }

    @PutMapping("/preferences")
    @Operation(summary = "Update user preferences", security = @SecurityRequirement(name = "Bearer"))
    public ResponseEntity<ApiResponse<UserPreferenceResponse>> updatePreferences(
            @Valid @RequestBody UserPreferenceRequest request) {
        UserPreferenceResponse preferences = userService.updateUserPreferences(request);
        return ResponseEntity.ok(ApiResponse.success("Preferences updated", preferences));
    }

    @GetMapping("/favorites")
    @Operation(summary = "Get user's favorite news", security = @SecurityRequirement(name = "Bearer"))
    public ResponseEntity<ApiResponse<List<NewsArticleResponse>>> getFavorites() {
        List<NewsArticleResponse> favorites = newsService.getUserFavorites();
        return ResponseEntity.ok(ApiResponse.success(favorites));
    }
}
