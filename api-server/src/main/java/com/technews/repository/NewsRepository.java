package com.technews.repository;

import com.technews.entity.News;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.time.LocalDate;
import java.util.List;

@Repository
public interface NewsRepository extends JpaRepository<News, Long> {

    List<News> findByPublishedDateOrderByFinalScoreDesc(LocalDate publishedDate);

    List<News> findByPublishedDateBetweenOrderByPublishedDateDescFinalScoreDesc(
            LocalDate startDate, LocalDate endDate);

    @Query("SELECT n FROM News n WHERE n.publishedDate < :date ORDER BY n.publishedDate DESC, n.finalScore DESC")
    List<News> findArchiveNews(@Param("date") LocalDate date);

    @Query("SELECT DISTINCT n.publishedDate FROM News n ORDER BY n.publishedDate DESC")
    List<LocalDate> findDistinctPublishedDates();
}
