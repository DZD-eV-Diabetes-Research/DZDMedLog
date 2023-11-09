package de.dzd.idom.drug.association;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.NonNull;

/**
 * hersteller.txt
 * 52;202301;A RSSL01;Albert Roussel
 */
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Producer {
    @Id
    @Column(name = "id")
    private String key;
    @NonNull
    private String name;
}
