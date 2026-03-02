package com.technews.entity;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "news")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class News {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 500)
    private String title;

    @Column(name = "translated_title", length = 500)
    private String translatedTitle;

    @Column(nullable = false, length = 1000)
    private String url;

    @Column(length = 100)
    private String source;

    @Column(length = 50)
    private String category;

    private Integer score;

    @Column(name = "llm_score", precision = 3, scale = 1)
    private BigDecimal llmScore;

    @Column(name = "final_score", precision = 4, scale = 3)
    private BigDecimal finalScore;

    @Column(columnDefinition = "TEXT")
    private String summary;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Column(name = "published_date")
    private LocalDate publishedDate;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
