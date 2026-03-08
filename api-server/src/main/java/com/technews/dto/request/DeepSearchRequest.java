package com.technews.dto.request;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeepSearchRequest {

    @NotBlank(message = "Article ID is required")
    private String articleId;

    @Min(value = 1, message = "Max iterations must be at least 1")
    @Max(value = 10, message = "Max iterations must not exceed 10")
    @Builder.Default
    private Integer maxIterations = 5;
}