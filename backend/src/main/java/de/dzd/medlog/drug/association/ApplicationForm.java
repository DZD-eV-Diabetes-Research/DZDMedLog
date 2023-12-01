package de.dzd.medlog.drug.association;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * applikationsform.txt
 * 52;202301;A;am Auge
 */
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ApplicationForm {
    @Id
    @Column(name = "id")
    private String abbreviation;
    private String name;
}
