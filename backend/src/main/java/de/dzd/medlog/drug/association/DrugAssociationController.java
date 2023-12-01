package de.dzd.medlog.drug.association;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping
@AllArgsConstructor
public class DrugAssociationController {
    private ApplicationFormRepository applicationFormRepository;
    private DosageFormRepository dosageFormRepository;
    private NormPackageSizeRepository normPackageSizeRepository;

    @RequestMapping("/application-forms")
    public List<ApplicationForm> getApplicationForms() {
        return applicationFormRepository.findAll();
    }

    @RequestMapping("/dosage-forms")
    public List<DosageForm> getDosageForms() {
        return dosageFormRepository.findAll();
    }

    @RequestMapping("/norm-package-sizes")
    public List<NormPackageSize> getNormPackageSizes() {
        return normPackageSizeRepository.findAll();
    }
}
