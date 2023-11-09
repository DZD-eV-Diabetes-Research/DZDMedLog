package de.dzd.idom.drug.association;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * atc-ai.txt
 * 52;202301;A08AA51;Phentermin und Topiramat
 */
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ATC {
    @Id
    @Column(name = "id")
    private String abbreviation;
    private String agent;
}
