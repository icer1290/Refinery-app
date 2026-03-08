package com.technews.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NewsArticleResponse {

    private UUID id;

    private String sourceName;

    private String sourceUrl;

    private String originalTitle;

    private String originalDescription;

    private String chineseTitle;

    private String chineseSummary;

    private String fullContent;

    // Scores
    private Float totalScore;
    private Float industryImpactScore;
    private Float milestoneScore;
    private Float attentionScore;

    // Timestamps
    private LocalDateTime publishedAt;
    private LocalDateTime processedAt;

    // User interaction
    private Boolean isFavorite;

    // DeepSearch Report
    private String deepsearchReport;
    private LocalDateTime deepsearchPerformedAt;
}