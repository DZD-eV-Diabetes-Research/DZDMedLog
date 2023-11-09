package de.dzd.idom.drug;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DrugRepository extends JpaRepository<Drug, Long> {
    List<Drug> findByNameContains(String name);
    Page<Drug> findAll(Pageable pageable);
    Page<Drug> findByNameContainingIgnoreCase(String name, Pageable pageable);
}
