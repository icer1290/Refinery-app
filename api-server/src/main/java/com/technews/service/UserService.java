package com.technews.service;

import com.technews.dto.request.UserPreferenceRequest;
import com.technews.dto.response.UserPreferenceResponse;
import com.technews.entity.User;
import com.technews.entity.UserPreference;
import com.technews.exception.ResourceNotFoundException;
import com.technews.repository.UserPreferenceRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserPreferenceRepository userPreferenceRepository;
    private final AuthService authService;
    private final ObjectMapper objectMapper;

    public UserPreferenceResponse getUserPreferences() {
        User user = authService.getCurrentUser();

        UserPreference preference = userPreferenceRepository.findByUserId(user.getId())
                .orElseGet(() -> UserPreference.builder()
                        .user(user)
                        .notificationEnabled(true)
                        .build());

        return convertToResponse(preference);
    }

    @Transactional
    public UserPreferenceResponse updateUserPreferences(UserPreferenceRequest request) {
        User user = authService.getCurrentUser();

        UserPreference preference = userPreferenceRepository.findByUserId(user.getId())
                .orElseGet(() -> UserPreference.builder()
                        .user(user)
                        .build());

        if (request.getPreferredCategories() != null) {
            preference.setPreferredCategories(request.getPreferredCategories());
        }

        if (request.getNotificationEnabled() != null) {
            preference.setNotificationEnabled(request.getNotificationEnabled());
        }

        preference = userPreferenceRepository.save(preference);

        return convertToResponse(preference);
    }

    private UserPreferenceResponse convertToResponse(UserPreference preference) {
        return UserPreferenceResponse.builder()
                .id(preference.getId())
                .preferredCategories(preference.getPreferredCategories())
                .notificationEnabled(preference.getNotificationEnabled())
                .build();
    }
}
