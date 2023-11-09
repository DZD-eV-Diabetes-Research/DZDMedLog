package de.dzd.idom.interview.event;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.*;

@Entity
@Data
@NoArgsConstructor
@RequiredArgsConstructor
@AllArgsConstructor
public class Event {
    @Id
    @NonNull
    private Long id;
    private String name;
    private String description;
}
