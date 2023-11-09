package de.dzd.idom.configuration;


import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface ConfigurationRepository extends JpaRepository<Configuration, Long> {

    Optional<Configuration> findByFileName(String fileName);
}
