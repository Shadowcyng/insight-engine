import requests
from bs4 import BeautifulSoup

def generate_unicode_grid(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all table cells
    cells = soup.find_all('td')
    # Remove header cells by skipping the first 3
    data_cells = [cell.get_text(strip=True) for cell in cells[3:]]
    
    # Group every 3 values (x, char, y)
    grid = {}
    max_x = max_y = 0
    for i in range(0, len(data_cells), 3):
        if i + 2 < len(data_cells):
            try:
                x = int(data_cells[i])
                char = data_cells[i + 1]
                y = int(data_cells[i + 2])
                grid[(x, y)] = char
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            except (ValueError, IndexError):
                continue
    
    # Create and print the grid
    output_grid = [[' ' for _ in range(max_x + 1)] for _ in range(max_y + 1)]
    for (x, y), char in grid.items():
        output_grid[y][x] = char
    for row in output_grid:
        print(''.join(row))

# Call the function
generate_unicode_grid("https://docs.google.com/document/d/e/2PACX-1vSvM5gDlNvt7npYHhp_XfsJvuntUhq184By5xO_pA4b_gCWeXb6dM6ZxwN8rE6S4ghUsCj2VKR21oEP/pub")