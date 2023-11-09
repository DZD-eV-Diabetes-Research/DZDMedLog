package de.dzd.idom.drug;

import de.dzd.idom.drug.association.ATCRepository;
import de.dzd.idom.drug.association.ProducerRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/drugs")
@RequiredArgsConstructor
@Slf4j
public class DrugController {
    private final DrugService drugService;
    private final ProducerRepository producerRepository;
    private final ATCRepository atcRepository;

    @GetMapping
    public Page<Drug> getDrugs(
            @RequestParam Optional<Integer> page,
            @RequestParam Optional<Integer> size,
            @RequestParam Optional<String> sortField,
            @RequestParam Optional<String> globalFilter,
            @RequestParam(defaultValue = "1") Integer sortOrder,
            @RequestParam(defaultValue = "") List<String[]> multiSortMeta
    ) {
        Pageable pageable;

        if (page.isEmpty() && size.isEmpty()) {
            pageable = Pageable.unpaged();
        } else {
            List<Sort.Order> orders = multiSortMeta.stream()
                    .map(order -> {
                        String property = order[0];
                        Sort.Direction direction = Integer.parseInt(order[1]) < 0 ? Sort.Direction.DESC : Sort.Direction.ASC;
                        return new Sort.Order(direction, property);
                    })
                    .toList();
            Sort sort;
            if (!orders.isEmpty()) {
                sort = Sort.by(orders);
            } else if (sortField.isPresent()) {
                Sort.Direction direction = sortOrder < 0 ? Sort.Direction.DESC : Sort.Direction.ASC;
                sort = Sort.by(direction, sortField.get());
            } else {
                sort = Sort.unsorted();
            }

            pageable = PageRequest.of(page.orElse(0), size.orElse(50), sort);
        }

        if (globalFilter.isPresent()) {
            return drugService.findByNameContainingIgnoreCase(globalFilter.get(), pageable);
        } else {
            return drugService.findAll(pageable);
        }
    }
    @PostMapping
    public ResponseEntity<Drug> createDrug(@RequestBody Drug drug) {
        if (drug.getAtc() != null) {
            atcRepository.save(drug.getAtc());
        }
        if (drug.getProducer() != null) {
            producerRepository.save(drug.getProducer());
        }
        drug.setIsCustom(true);
       Drug saved = drugService.save(drug);
       return new ResponseEntity<>(saved, HttpStatus.CREATED);
    }
    @GetMapping("/{id}")
    public Drug getDrugById(@PathVariable Long id) {
        return drugService.findById(id).orElse(null);
    }
    @GetMapping("/{name}")
    public List<Drug> getDrugsByName(@PathVariable String name) {
        return drugService.findByNameContains(name);
    }
}
