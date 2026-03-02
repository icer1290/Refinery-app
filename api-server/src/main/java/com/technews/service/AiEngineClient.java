package com.technews.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiEngineClient {

    @Value("${ai-engine.base-url}")
    private String aiEngineUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> fetchTodayNews(LocalDate date) {
        try {
            String url = aiEngineUrl + "/internal/news/today";
            if (date != null) {
                url += "?date=" + date.toString();
            }

            log.info("Fetching news from AI engine: {}", url);
            Map<String, Object> response = restTemplate.getForObject(url, Map.class);

            if (response != null && response.containsKey("news")) {
                return (List<Map<String, Object>>) response.get("news");
            }
            return List.of();
        } catch (Exception e) {
            log.error("Failed to fetch news from AI engine: {}", e.getMessage());
            return List.of();
        }
    }

    public void triggerIngest() {
        try {
            String url = aiEngineUrl + "/internal/ingest";
            log.info("Triggering ingest: {}", url);
            restTemplate.postForObject(url, null, Map.class);
        } catch (Exception e) {
            log.error("Failed to trigger ingest: {}", e.getMessage());
        }
    }

    public void triggerScore(List<String> newsIds) {
        try {
            String url = aiEngineUrl + "/internal/score";
            log.info("Triggering score for {} news items", newsIds.size());
            restTemplate.postForObject(url, Map.of("news_ids", newsIds), Map.class);
        } catch (Exception e) {
            log.error("Failed to trigger score: {}", e.getMessage());
        }
    }

    public void triggerSummarize(List<String> newsIds) {
        try {
            String url = aiEngineUrl + "/internal/summarize";
            log.info("Triggering summarize for {} news items", newsIds.size());
            restTemplate.postForObject(url, Map.of("news_ids", newsIds), Map.class);
        } catch (Exception e) {
            log.error("Failed to trigger summarize: {}", e.getMessage());
        }
    }
}
