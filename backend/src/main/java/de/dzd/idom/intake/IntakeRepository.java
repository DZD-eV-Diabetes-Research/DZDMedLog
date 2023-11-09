package de.dzd.idom.intake;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface IntakeRepository extends JpaRepository<Intake, Long> {

}
