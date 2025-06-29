import pygame
import random
from engine.battle import Party, battle_round, is_battle_over, start_battle, prepare_battle

def start_game(pokemon_df, move_lookup, type_chart):
    WIDTH, HEIGHT = 800, 800
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

    # Get who goes first and intro logs
    log_lines = []
    battle_state = "preview"  # "preview" -> "pick_starter" -> "battle"
    selected_index = None

    intro_log = prepare_battle(player_party, ai_party)
    log_lines.extend(intro_log)

    battle_over = False
    round_num = 1

    running = True
    while running:
        screen.fill(WHITE)

        # === PREVIEW PHASE ===
        if battle_state == "preview":
            instruct = FONT.render("Click a Pokémon to send out!", True, BLACK)
            screen.blit(instruct, (280, 100))

            # Your Team
            team_text = FONT.render("Your Team:", True, BLACK)
            screen.blit(team_text, (50, 140))
            for i, mon in enumerate(player_party.pokemons):
                mon_text = FONT.render(f"{i+1}. {mon.name} (HP: {mon.hp})", True, BLACK)
                screen.blit(mon_text, (70, 170 + i * 25))

            # Opponent's Team
            foe_text = FONT.render("Opponent's Team:", True, BLACK)
            screen.blit(foe_text, (500, 140))
            for i, mon in enumerate(ai_party.pokemons):
                # Show name or hide if you want mystery
                enemy_text = FONT.render(f"{i+1}. {mon.name}", True, BLACK)
                screen.blit(enemy_text, (520, 170 + i * 25))

        # === BATTLE PHASE ===
        elif battle_state == "battle":
            # Draw active Pokémon and HP
            player_active = player_party.active
            ai_active = ai_party.active
            pygame.draw.rect(screen, GRAY, (50, 50, 700, 100))
            player_text = FONT.render(f"You: {player_active.name} (HP: {player_active.hp})", True, BLACK)
            ai_text = FONT.render(f"Foe: {ai_active.name} (HP: {ai_active.hp})", True, BLACK)
            screen.blit(player_text, (60, 60))
            screen.blit(ai_text, (60, 90))

            # Draw move button
            if not battle_over:
                move_buttons = []
                for i, move in enumerate(player_party.active.moves):
                    if move == "-":
                        continue
                    btn_rect = pygame.Rect(250, 200 + i * 60, 300, 40)
                    pygame.draw.rect(screen, GRAY, btn_rect)
                    pygame.draw.rect(screen, BLACK, btn_rect, 2)
                    label = FONT.render(move, True, BLACK)
                    screen.blit(label, (btn_rect.x + 10, btn_rect.y + 10))
                    move_buttons.append((btn_rect, move))
            else:
                result_text = FONT.render("Battle Over! Click anywhere to exit.", True, (100, 0, 0))
                screen.blit(result_text, (250, 200))
        elif battle_state == "switch":
            instruct = FONT.render("⚠️ Choose a Pokémon to switch in!", True, BLACK)
            screen.blit(instruct, (250, 100))

            for i, mon in enumerate(player_party.pokemons):
                y = 160 + i * 40
                mon_rect = pygame.Rect(70, y, 400, 35)
                bg_color = GRAY if mon.is_fainted() else WHITE
                pygame.draw.rect(screen, bg_color, mon_rect)
                pygame.draw.rect(screen, BLACK, mon_rect, 2)
                
                mon_status = f"{i + 1}. {mon.name} (HP: {mon.hp})"
                if mon.is_fainted():
                    mon_status += " - Fainted"
                mon_text = FONT.render(mon_status, True, BLACK)
                screen.blit(mon_text, (mon_rect.x + 10, mon_rect.y + 5))
        # === Draw battle log ===
        y_offset = 400
        for line in log_lines[-10:]:
            rendered = FONT.render(line, True, BLACK)
            screen.blit(rendered, (40, y_offset))
            y_offset += 25

        # === Handle events ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if battle_state == "preview":
                    # Detect which Pokémon was clicked
                    for i in range(6):
                        y = 180 + i * 25
                        if 70 <= event.pos[0] <= 500 and y <= event.pos[1] <= y + 20:
                            selected_index = i
                            player_party.active_index = i
                            log_lines.append(f"➡️ You send out {player_party.active.name}!")
                            player_first = random.choice([True, False])
                            log_lines.append(f"{'You' if player_first else 'Opponent'} will go first!")
                            battle_state = "battle"
                            break

                elif battle_state == "battle":
                    if battle_over:
                        running = False
                    elif not battle_over:
                        for btn_rect, move_name in move_buttons:
                            if btn_rect.collidepoint(event.pos):
                                log_lines.append(f"--- Round {round_num} ---")
                                round_log = battle_round(player_party, ai_party, move_lookup, type_chart, player_move=move_name)
                                log_lines.extend(round_log)

                                if player_party.active.is_fainted():
                                    battle_state = "switch"
                                if ai_party.active.is_fainted():
                                    ai_party.switch_to_next()
                                if is_battle_over(player_party, ai_party):
                                    winner = "You" if not ai_party.has_available() else "AI"
                                    log_lines.append(f"Battle Over! Winner: {winner}")
                                    battle_over = True
                                round_num += 1
                                break
                elif battle_state == "switch":
                    for i, mon in enumerate(player_party.pokemons):
                        y = 180 + i * 30
                        if 70 <= event.pos[0] <= 370 and y <= event.pos[1] <= y + 25:
                            if not mon.is_fainted():
                                player_party.active_index = i
                                log_lines.append(f"You sent out {mon.name}!")
                                battle_state = "battle"
                                break

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
