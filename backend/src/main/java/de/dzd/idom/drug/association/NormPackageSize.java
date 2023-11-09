package de.dzd.idom.drug.association;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.NonNull;

/**
 * normpackungsgroessen.txt
 * 52;202301;*;freies Hilfsmittel
 */
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NormPackageSize {
    @Id
    private String id;
    @NonNull
    private String name;
}
