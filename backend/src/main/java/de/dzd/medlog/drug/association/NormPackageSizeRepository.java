package de.dzd.medlog.drug.association;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface NormPackageSizeRepository extends JpaRepository<NormPackageSize, String> {

}
