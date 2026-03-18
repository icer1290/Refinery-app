package com.technews.repository;

import com.technews.entity.DeepGraphAnalysis;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface DeepGraphAnalysisRepository extends JpaRepository<DeepGraphAnalysis, UUID> {

    Page<DeepGraphAnalysis> findByUserIdOrderByCreatedAtDesc(Long userId, Pageable pageable);

    Optional<DeepGraphAnalysis> findByIdAndUserId(UUID id, Long userId);
}