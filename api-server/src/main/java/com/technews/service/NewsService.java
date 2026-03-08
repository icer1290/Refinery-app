package com.technews.service;

import com.technews.dto.response.NewsArticleResponse;
import com.technews.dto.response.SimilarArticleResponse;
import com.technews.entity.Favorite;
import com.technews.entity.NewsArticle;
import com.technews.entity.User;
import com.technews.exception.ResourceNotFoundException;
import com.technews.repository.ArticleEmbeddingRepository;
import com.technews.repository.FavoriteRepository;
import com.technews.repository.NewsArticleRepository;
import com.technews.repository.VectorSearchRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class NewsService {

    private final NewsArticleRepository newsArticleRepository;
    private final FavoriteRepository favoriteRepository;
    private final ArticleEmbeddingRepository articleEmbeddingRepository;
    private final VectorSearchRepository vectorSearchRepository;
    private final AuthService authService;

    public List<NewsArticleResponse> getTodayNews() {
        LocalDate today = LocalDate.now();
        LocalDateTime startOfDay = today.atStartOfDay();
        LocalDateTime endOfDay = today.atTime(LocalTime.MAX);

        List<NewsArticle> articles = newsArticleRepository.findTodayNews(startOfDay, endOfDay);
        return convertToResponse(articles, null);
    }

    public List<NewsArticleResponse> getTodayNewsWithFavorites(Long userId) {
        LocalDate today = LocalDate.now();
        LocalDateTime startOfDay = today.atStartOfDay();
        LocalDateTime endOfDay = today.atTime(LocalTime.MAX);

        List<NewsArticle> articles = newsArticleRepository.findTodayNews(startOfDay, endOfDay);
        return convertToResponse(articles, userId);
    }

    public List<NewsArticleResponse> getArchiveNews(LocalDate startDate, LocalDate endDate) {
        if (startDate == null) {
            startDate = LocalDate.now().minusMonths(1);
        }
        if (endDate == null) {
            endDate = LocalDate.now();
        }

        LocalDateTime start = startDate.atStartOfDay();
        LocalDateTime end = endDate.atTime(LocalTime.MAX);

        List<NewsArticle> articles = newsArticleRepository.findByPublishedAtBetweenOrderByPublishedAtDescTotalScoreDesc(start, end);
        return convertToResponse(articles, null);
    }

    public List<NewsArticleResponse> getArchiveNewsWithFavorites(LocalDate startDate, LocalDate endDate, Long userId) {
        if (startDate == null) {
            startDate = LocalDate.now().minusMonths(1);
        }
        if (endDate == null) {
            endDate = LocalDate.now();
        }

        LocalDateTime start = startDate.atStartOfDay();
        LocalDateTime end = endDate.atTime(LocalTime.MAX);

        List<NewsArticle> articles = newsArticleRepository.findByPublishedAtBetweenOrderByPublishedAtDescTotalScoreDesc(start, end);
        return convertToResponse(articles, userId);
    }

    public NewsArticleResponse getNewsById(UUID id) {
        NewsArticle article = newsArticleRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("NewsArticle", "id", id));
        return convertToResponse(article, null);
    }

    public NewsArticleResponse getNewsByIdWithFavorite(UUID id, Long userId) {
        NewsArticle article = newsArticleRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("NewsArticle", "id", id));
        return convertToResponse(article, userId);
    }

    public List<LocalDate> getAvailableDates() {
        return newsArticleRepository.findDistinctPublishedDates();
    }

    @Transactional
    public void addFavorite(UUID articleId) {
        User user = authService.getCurrentUser();
        NewsArticle article = newsArticleRepository.findById(articleId)
                .orElseThrow(() -> new ResourceNotFoundException("NewsArticle", "id", articleId));

        if (!favoriteRepository.existsByUserIdAndArticleId(user.getId(), articleId)) {
            Favorite favorite = Favorite.builder()
                    .user(user)
                    .article(article)
                    .build();
            favoriteRepository.save(favorite);
        }
    }

    @Transactional
    public void removeFavorite(UUID articleId) {
        User user = authService.getCurrentUser();
        favoriteRepository.deleteByUserIdAndArticleId(user.getId(), articleId);
    }

    public List<NewsArticleResponse> getUserFavorites() {
        User user = authService.getCurrentUser();
        List<Favorite> favorites = favoriteRepository.findByUserIdOrderByCreatedAtDesc(user.getId());

        List<NewsArticle> articles = favorites.stream()
                .map(Favorite::getArticle)
                .collect(Collectors.toList());

        return convertToResponse(articles, user.getId());
    }

    public List<SimilarArticleResponse> findSimilarArticles(UUID articleId, int limit, double threshold) {
        // Check if the article exists
        newsArticleRepository.findById(articleId)
                .orElseThrow(() -> new ResourceNotFoundException("NewsArticle", "id", articleId));

        // Check if the article has an embedding
        if (!articleEmbeddingRepository.findByArticleId(articleId).isPresent()) {
            return List.of();
        }

        Long userId = null;
        try {
            userId = authService.getCurrentUser().getId();
        } catch (Exception e) {
            // User not authenticated, proceed without favorite info
        }

        List<VectorSearchRepository.SimilarArticleResult> results =
                vectorSearchRepository.findSimilarArticles(articleId, limit, threshold);

        final Long finalUserId = userId;
        return results.stream()
                .map(result -> convertToSimilarResponse(result, finalUserId))
                .collect(Collectors.toList());
    }

    private List<NewsArticleResponse> convertToResponse(List<NewsArticle> articles, Long userId) {
        return articles.stream()
                .map(article -> convertToResponse(article, userId))
                .collect(Collectors.toList());
    }

    private NewsArticleResponse convertToResponse(NewsArticle article, Long userId) {
        boolean isFavorite = false;
        if (userId != null) {
            isFavorite = favoriteRepository.existsByUserIdAndArticleId(userId, article.getId());
        }

        return NewsArticleResponse.builder()
                .id(article.getId())
                .sourceName(article.getSourceName())
                .sourceUrl(article.getSourceUrl())
                .originalTitle(article.getOriginalTitle())
                .originalDescription(article.getOriginalDescription())
                .chineseTitle(article.getChineseTitle())
                .chineseSummary(article.getChineseSummary())
                .fullContent(article.getFullContent())
                .totalScore(article.getTotalScore())
                .industryImpactScore(article.getIndustryImpactScore())
                .milestoneScore(article.getMilestoneScore())
                .attentionScore(article.getAttentionScore())
                .publishedAt(article.getPublishedAt())
                .processedAt(article.getProcessedAt())
                .isFavorite(isFavorite)
                .deepsearchReport(article.getDeepsearchReport())
                .deepsearchPerformedAt(article.getDeepsearchPerformedAt())
                .build();
    }

    private SimilarArticleResponse convertToSimilarResponse(VectorSearchRepository.SimilarArticleResult result, Long userId) {
        boolean isFavorite = false;
        if (userId != null) {
            isFavorite = favoriteRepository.existsByUserIdAndArticleId(userId, result.getId());
        }

        return SimilarArticleResponse.builder()
                .id(result.getId())
                .sourceName(result.getSourceName())
                .sourceUrl(result.getSourceUrl())
                .originalTitle(result.getOriginalTitle())
                .originalDescription(result.getOriginalDescription())
                .chineseTitle(result.getChineseTitle())
                .chineseSummary(result.getChineseSummary())
                .fullContent(result.getFullContent())
                .totalScore(result.getTotalScore())
                .industryImpactScore(result.getIndustryImpactScore())
                .milestoneScore(result.getMilestoneScore())
                .attentionScore(result.getAttentionScore())
                .publishedAt(result.getPublishedAt())
                .processedAt(result.getProcessedAt())
                .similarity(result.getSimilarity())
                .isFavorite(isFavorite)
                .build();
    }
}