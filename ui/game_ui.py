import pygame
import random
from engine.battle import Party, battle_round, is_battle_over

def start_game(pokemon_df, move_lookup, type_chart):
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pokémon Battle")

    FONT = pygame.font.SysFont('Arial', 20)
    WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
    clock = pygame.time.Clock()

    # Generate teams
    player_team = pokemon_df.sample(n=6).reset_index(drop=True).to_dict(orient="records")
    ai_team = pokemon_df.sample(n=6).reset_index(drop=True).to_dict(orient="records")
    player_party = Party(player_team)
    ai_party = Party(ai_team)

    log_lines = []
    battle_over = False
    round_num = 1

    running = True
    while running:
        screen.fill(WHITE)

        # Draw active Pokémon and HP
        player_active = player_party.active
        ai_active = ai_party.active
        pygame.draw.rect(screen, GRAY, (50, 50, 700, 100))
        player_text = FONT.render(f"You: {player_active.name} (HP: {player_active.hp})", True, BLACK)
        ai_text = FONT.render(f"Foe: {ai_active.name} (HP: {ai_active.hp})", True, BLACK)
        screen.blit(player_text, (60, 60))
        screen.blit(ai_text, (60, 90))

        # Draw move button if battle ongoing
        if not battle_over:
            move_button = pygame.Rect(300, 200, 200, 50)
            pygame.draw.rect(screen, GRAY, move_button)
            pygame.draw.rect(screen, BLACK, move_button, 2)
            move_label = FONT.render("Fight!", True, BLACK)
            screen.blit(move_label, (move_button.x + 70, move_button.y + 15))
        else:
            result_text = FONT.render("Battle Over! Click anywhere to exit.", True, (100, 0, 0))
            screen.blit(result_text, (250, 200))

        # Draw battle log
        y_offset = 280
        for line in log_lines[-10:]:
            rendered = FONT.render(line, True, BLACK)
            screen.blit(rendered, (40, y_offset))
            y_offset += 25

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if battle_over:
                    running = False
                elif not battle_over and move_button.collidepoint(event.pos):
                    log_lines.append(f"--- Round {round_num} ---")
                    round_log = battle_round(player_party, ai_party, move_lookup, type_chart)
                    log_lines.extend(round_log)
                    if player_party.active.is_fainted():
                        player_party.switch_to_next()
                    if ai_party.active.is_fainted():
                        ai_party.switch_to_next()
                    if is_battle_over(player_party, ai_party):
                        winner = "You" if ai_party.has_available() == False else "AI"
                        log_lines.append(f"Battle Over! Winner: {winner}")
                        battle_over = True
                    round_num += 1

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

