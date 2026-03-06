package com.technews.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NewsResponse {

    private Long id;

    private String title;

    private String translatedTitle;

    private String url;

    private String source;

    private String category;

    private Integer score;

    private BigDecimal llmScore;

    private BigDecimal finalScore;

    private String summary;

    private LocalDate publishedDate;

    private Boolean isFavorite;
}
