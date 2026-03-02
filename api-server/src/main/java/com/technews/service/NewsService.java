package com.technews.service;

import com.technews.dto.response.NewsResponse;
import com.technews.entity.Favorite;
import com.technews.entity.News;
import com.technews.entity.User;
import com.technews.exception.ResourceNotFoundException;
import com.technews.repository.FavoriteRepository;
import com.technews.repository.NewsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class NewsService {

    private final NewsRepository newsRepository;
    private final FavoriteRepository favoriteRepository;
    private final AuthService authService;
    private final AiEngineClient aiEngineClient;

    public List<NewsResponse> getTodayNews() {
        LocalDate today = LocalDate.now();

        List<News> news = newsRepository.findByPublishedDateOrderByFinalScoreDesc(today);

        if (news.isEmpty()) {
            List<Map<String, Object>> aiNews = aiEngineClient.fetchTodayNews(today);
            if (!aiNews.isEmpty()) {
                news = saveNewsFromAiEngine(aiNews);
            }
        }

        return convertToResponse(news, null);
    }

    public List<NewsResponse> getTodayNewsWithFavorites(Long userId) {
        LocalDate today = LocalDate.now();

        List<News> news = newsRepository.findByPublishedDateOrderByFinalScoreDesc(today);

        if (news.isEmpty()) {
            List<Map<String, Object>> aiNews = aiEngineClient.fetchTodayNews(today);
            if (!aiNews.isEmpty()) {
                news = saveNewsFromAiEngine(aiNews);
            }
        }

        return convertToResponse(news, userId);
    }

    public List<NewsResponse> getArchiveNews(LocalDate startDate, LocalDate endDate) {
        if (startDate == null) {
            startDate = LocalDate.now().minusMonths(1);
        }
        if (endDate == null) {
            endDate = LocalDate.now();
        }

        List<News> news = newsRepository.findByPublishedDateBetweenOrderByPublishedDateDescFinalScoreDesc(
                startDate, endDate);

        return convertToResponse(news, null);
    }

    public List<NewsResponse> getArchiveNewsWithFavorites(LocalDate startDate, LocalDate endDate, Long userId) {
        if (startDate == null) {
            startDate = LocalDate.now().minusMonths(1);
        }
        if (endDate == null) {
            endDate = LocalDate.now();
        }

        List<News> news = newsRepository.findByPublishedDateBetweenOrderByPublishedDateDescFinalScoreDesc(
                startDate, endDate);

        return convertToResponse(news, userId);
    }

    public NewsResponse getNewsById(Long id) {
        News news = newsRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("News", "id", id));
        return convertToResponse(news, null);
    }

    public NewsResponse getNewsByIdWithFavorite(Long id, Long userId) {
        News news = newsRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("News", "id", id));
        return convertToResponse(news, userId);
    }

    public List<LocalDate> getAvailableDates() {
        return newsRepository.findDistinctPublishedDates();
    }

    @Transactional
    public void addFavorite(Long newsId) {
        User user = authService.getCurrentUser();
        News news = newsRepository.findById(newsId)
                .orElseThrow(() -> new ResourceNotFoundException("News", "id", newsId));

        if (!favoriteRepository.existsByUserIdAndNewsId(user.getId(), newsId)) {
            Favorite favorite = Favorite.builder()
                    .user(user)
                    .news(news)
                    .build();
            favoriteRepository.save(favorite);
        }
    }

    @Transactional
    public void removeFavorite(Long newsId) {
        User user = authService.getCurrentUser();
        favoriteRepository.deleteByUserIdAndNewsId(user.getId(), newsId);
    }

    public List<NewsResponse> getUserFavorites() {
        User user = authService.getCurrentUser();
        List<Favorite> favorites = favoriteRepository.findByUserIdOrderByCreatedAtDesc(user.getId());

        List<News> newsList = favorites.stream()
                .map(Favorite::getNews)
                .collect(Collectors.toList());

        return convertToResponse(newsList, user.getId());
    }

    @SuppressWarnings("unchecked")
    @Transactional
    public List<News> saveNewsFromAiEngine(List<Map<String, Object>> aiNews) {
        List<News> newsList = aiNews.stream().map(item -> {
            BigDecimal llmScore = null;
            Object llmScoreObj = item.get("llm_score");
            if (llmScoreObj instanceof Number) {
                llmScore = BigDecimal.valueOf(((Number) llmScoreObj).doubleValue());
            }

            BigDecimal finalScore = null;
            Object finalScoreObj = item.get("final_score");
            if (finalScoreObj instanceof Number) {
                finalScore = BigDecimal.valueOf(((Number) finalScoreObj).doubleValue());
            }

            String publishedDate = (String) item.get("published_date");
            LocalDate publishedDateValue = publishedDate != null ? LocalDate.parse(publishedDate) : LocalDate.now();

            return News.builder()
                    .title((String) item.get("title"))
                    .translatedTitle((String) item.get("translated_title"))
                    .url((String) item.get("url"))
                    .source((String) item.get("source"))
                    .category((String) item.get("category"))
                    .score((Integer) item.get("score"))
                    .llmScore(llmScore)
                    .finalScore(finalScore)
                    .summary((String) item.get("summary"))
                    .publishedDate(publishedDateValue)
                    .build();
        }).collect(Collectors.toList());

        return newsRepository.saveAll(newsList);
    }

    private List<NewsResponse> convertToResponse(List<News> newsList, Long userId) {
        return newsList.stream()
                .map(news -> convertToResponse(news, userId))
                .collect(Collectors.toList());
    }

    private NewsResponse convertToResponse(News news, Long userId) {
        boolean isFavorite = false;
        if (userId != null) {
            isFavorite = favoriteRepository.existsByUserIdAndNewsId(userId, news.getId());
        }

        return NewsResponse.builder()
                .id(news.getId())
                .title(news.getTitle())
                .translatedTitle(news.getTranslatedTitle())
                .url(news.getUrl())
                .source(news.getSource())
                .category(news.getCategory())
                .score(news.getScore())
                .llmScore(news.getLlmScore())
                .finalScore(news.getFinalScore())
                .summary(news.getSummary())
                .publishedDate(news.getPublishedDate())
                .isFavorite(isFavorite)
                .build();
    }
}
