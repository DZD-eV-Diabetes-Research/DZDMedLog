package de.dzd.idom.drug;

import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class DrugService {
    private final DrugRepository drugRepository;

    public Page<Drug> findAll(Pageable pageable) {
        return drugRepository.findAll(pageable);
    }
    public Page<Drug> findByNameContainingIgnoreCase(String searchFilter, Pageable pageable) {
        return drugRepository.findByNameContainingIgnoreCase(searchFilter, pageable);
    }
    public Drug save(Drug drug) {
        return drugRepository.save(drug);
    }
    public List<Drug> saveAll(List<Drug> drugs) {
        return drugRepository.saveAll(drugs);
    }
    public void deleteAll(List<Drug> drugs) {
        drugRepository.deleteAll(drugs);
    }
    public Optional<Drug> findById(Long pharmaceuticalCentralNumber) {
        return drugRepository.findById(pharmaceuticalCentralNumber);
    }
    public List<Drug> findByNameContains(String name) {
        return drugRepository.findByNameContains(name);
    }
}
