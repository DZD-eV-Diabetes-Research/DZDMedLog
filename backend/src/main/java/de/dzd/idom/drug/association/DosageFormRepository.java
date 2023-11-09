package de.dzd.idom.drug.association;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DosageFormRepository extends JpaRepository<DosageForm, String> {

}
