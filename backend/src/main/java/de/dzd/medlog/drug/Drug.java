package de.dzd.medlog.drug;

import de.dzd.medlog.drug.association.*;
import jakarta.persistence.*;
import lombok.*;

/**
 * stamm.txt
 */
@Entity
@Data
@RequiredArgsConstructor
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Drug {
    @Id
    @NonNull
    private Long pharmaceuticalCentralNumber;
    @ManyToOne
    private ATC atc;
    private String name;
    @ManyToOne
    private DosageForm dosageForm;
    @ManyToOne
    private ApplicationForm applicationForm;
    private Integer packageSize;
    @ManyToOne
    private NormPackageSize normPackageSize;
    @ManyToOne
    private Producer producer;
    private long priceInCents;
    private long fixedPriceInCents;
    private Boolean isCustom;
}
