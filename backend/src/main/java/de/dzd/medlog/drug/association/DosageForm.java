package de.dzd.medlog.drug.association;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * darrform.txt
 * 52;202301;AEO;Ätherisches Öl
 */
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DosageForm {
    @Id
    @Column(name = "id")
    private String abbreviation;
    private String name;
}
