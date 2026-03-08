package com.technews.repository;

import com.technews.entity.Favorite;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface FavoriteRepository extends JpaRepository<Favorite, Long> {

    List<Favorite> findByUserIdOrderByCreatedAtDesc(Long userId);

    Optional<Favorite> findByUserIdAndArticleId(Long userId, UUID articleId);

    boolean existsByUserIdAndArticleId(Long userId, UUID articleId);

    void deleteByUserIdAndArticleId(Long userId, UUID articleId);
}
