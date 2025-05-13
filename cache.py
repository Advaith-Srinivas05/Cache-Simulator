import customtkinter as ctk
from collections import OrderedDict

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class Cache:
    def __init__(self, size, policy, cache_type, set_count=1):
        self.size = size
        self.policy = policy
        self.cache_type = cache_type
        self.set_count = set_count
        self.hits = 0
        self.misses = 0

        if cache_type == "Fully Associative":
            if policy == "FIFO":
                self.cache = [None] * size
                self.insert_order = []  
            else: 
                self.cache = [None] * size  
                self.lru_tracker = OrderedDict()  
                self.next_position = 0  

        elif cache_type == "Direct Mapped":
            self.cache = [None] * size

        elif cache_type == "Set Associative":
            self.sets = []
            blocks_per_set = size // set_count if set_count > 0 else 1
            for i in range(set_count):
                if policy == "FIFO":
                    
                    self.sets.append({
                        'cache': [None] * blocks_per_set,
                        'insert_order': []
                    })
                else:  
                    self.sets.append({
                        'cache': [None] * blocks_per_set,
                        'lru_tracker': OrderedDict(),
                        'next_position': 0
                    })
            self.blocks_per_set = blocks_per_set

    def access(self, address):
        addr = int(address)

        if self.cache_type == "Fully Associative":
            if self.policy == "FIFO":
                
                if addr in self.cache:
                    position = self.cache.index(addr)
                    self.hits += 1
                else:
                    self.misses += 1
                    
                    if None in self.cache:
                        position = self.cache.index(None)
                        self.insert_order.append(position)
                    else:
                        
                        position = self.insert_order.pop(0)
                        self.insert_order.append(position)
                    
                    self.cache[position] = addr
            else:  
                if addr in self.cache:
                    position = self.cache.index(addr)
                    self.hits += 1
                    
                    if addr in self.lru_tracker:
                        del self.lru_tracker[addr]
                    self.lru_tracker[addr] = position  
                else:
                    self.misses += 1
                    
                    if None in self.cache:
                        position = self.cache.index(None)
                        self.cache[position] = addr
                        self.lru_tracker[addr] = position
                    else:
                        lru_addr, lru_pos = next(iter(self.lru_tracker.items()))
                        del self.lru_tracker[lru_addr]
                        self.cache[lru_pos] = addr
                        self.lru_tracker[addr] = lru_pos

        elif self.cache_type == "Direct Mapped":
            index = addr % self.size
            if self.cache[index] == addr:
                self.hits += 1
            else:
                self.misses += 1
                self.cache[index] = addr

        elif self.cache_type == "Set Associative":
            set_index = addr % self.set_count
            target_set = self.sets[set_index]

            if self.policy == "FIFO":
                
                if addr in target_set['cache']:
                    self.hits += 1
                else:
                    self.misses += 1
                    
                    if None in target_set['cache']:
                        position = target_set['cache'].index(None)
                        target_set['insert_order'].append(position)
                    else:
                        position = target_set['insert_order'].pop(0)
                        target_set['insert_order'].append(position)
                    
                    target_set['cache'][position] = addr
            else:
                cache_array = target_set['cache']
                lru_tracker = target_set['lru_tracker']
                
                if addr in cache_array:
                    position = cache_array.index(addr)
                    self.hits += 1
                    
                    if addr in lru_tracker:
                        del lru_tracker[addr]
                    lru_tracker[addr] = position  
                else:
                    self.misses += 1
                    
                    if None in cache_array:
                        position = cache_array.index(None)
                        cache_array[position] = addr
                        lru_tracker[addr] = position
                    else:
                        lru_addr, lru_pos = next(iter(lru_tracker.items()))
                        del lru_tracker[lru_addr]
                        cache_array[lru_pos] = addr
                        lru_tracker[addr] = lru_pos

    def get_stats(self):
        total = self.hits + self.misses
        return self.hits, self.misses, round(self.hits / total, 2) if total > 0 else 0

    def get_visual(self):
        if self.cache_type == "Fully Associative":
            return self.cache

        elif self.cache_type == "Direct Mapped":
            return self.cache

        elif self.cache_type == "Set Associative":
            visual = []
            for i, s in enumerate(self.sets):
                entries = s['cache']
                visual.append((f"Set {i}", entries))
            return visual


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cache Simulator")
        self.geometry("900x600")  

        self.addresses = []
        self.policy = ctk.StringVar(value="FIFO")
        self.cache_type = ctk.StringVar(value="Fully Associative")
        self.cache_size = ctk.StringVar(value="4")  
        self.set_count = ctk.StringVar(value="2")
        self.dark_bg = "#2b2b2b"
        
        self.hex_mode = ctk.BooleanVar(value=False)
        
        self.active_cache = None
        
        self.main_layout = ctk.CTkFrame(self)
        self.main_layout.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.left_frame = ctk.CTkFrame(self.main_layout)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.right_frame = ctk.CTkFrame(self.main_layout)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.create_widgets()
        
        self.create_new_cache()

    def validate_int(self, value, default=1):
        if value.strip() == "":
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def create_widgets(self):
        config_frame = ctk.CTkFrame(self.left_frame)
        config_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(config_frame, text="Cache Configuration", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(5, 15), sticky="w")

        ctk.CTkLabel(config_frame, text="Replacement Policy:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        policy_menu = ctk.CTkOptionMenu(config_frame, variable=self.policy, values=["FIFO", "LRU"], 
                                     command=self.on_config_change)
        policy_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(config_frame, text="Cache Type:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        type_menu = ctk.CTkOptionMenu(config_frame, variable=self.cache_type, 
                                     values=["Fully Associative", "Direct Mapped", "Set Associative"], 
                                     command=self.on_type_change)
        type_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(config_frame, text="Cache Size:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        size_entry = ctk.CTkEntry(config_frame, textvariable=self.cache_size)
        size_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        size_entry.bind("<FocusOut>", lambda e: self.on_config_change())
        
        self.set_label = ctk.CTkLabel(config_frame, text="Set Count:")
        self.set_entry = ctk.CTkEntry(config_frame, textvariable=self.set_count)
        self.set_entry.bind("<FocusOut>", lambda e: self.on_config_change())
        
        ctk.CTkLabel(config_frame, text="Input Mode:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        hex_toggle_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        hex_toggle_frame.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(hex_toggle_frame, text="Decimal").pack(side="left", padx=(0, 5))
        self.hex_switch = ctk.CTkSwitch(hex_toggle_frame, text="Hex", variable=self.hex_mode, command=self.toggle_hex_mode)
        self.hex_switch.pack(side="left")
        
        address_frame = ctk.CTkFrame(self.left_frame)
        address_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(address_frame, text="Address Sequence", 
                    font=("Arial", 16, "bold")).pack(anchor="w", pady=(5, 10))
        
        entry_row = ctk.CTkFrame(address_frame, fg_color=self.dark_bg)
        entry_row.pack(fill="x")
        
        self.input_mode_label = ctk.CTkLabel(entry_row, text="DEC", width=30, 
                                            fg_color="#3b3b3b", corner_radius=5,
                                            text_color="white", font=("Arial", 12, "bold"))
        self.input_mode_label.pack(side="left", padx=(0, 5))
        
        self.addr_entry = ctk.CTkEntry(entry_row, placeholder_text="Enter address")
        self.addr_entry.pack(side="left", padx=5, expand=True, fill="x")
        self.addr_entry.bind("<Return>", lambda e: self.add_address())
        
        ctk.CTkButton(entry_row, text="Add Address", command=self.add_address).pack(side="right", padx=5)

        self.addr_display = ctk.CTkTextbox(address_frame, height=120, width=300)
        self.addr_display.insert("end", "Address Sequence:\n")
        self.addr_display.configure(state="disabled")
        self.addr_display.pack(pady=10, fill="x")
               
        button_row = ctk.CTkFrame(address_frame, fg_color=self.dark_bg)
        button_row.pack(fill="x", pady=(0, 5))
        
        ctk.CTkButton(
            button_row,
            text="Reset Cache",
            command=self.create_new_cache,
            fg_color="#B22222",
            hover_color="#8B0000" 
        ).pack(side="right", padx=5)
 
        ctk.CTkLabel(self.right_frame, text="Simulation Results", 
                    font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5), padx=10)
        
        self.stats_label = ctk.CTkLabel(self.right_frame, 
                                       text="Hits: 0  Misses: 0  Hit Ratio: 0.00",
                                       font=("Arial", 14))
        self.stats_label.pack(pady=(5, 10), padx=10, anchor="w")
        
        visual_container = ctk.CTkFrame(self.right_frame, bg_color=self.dark_bg)
        visual_container.pack(pady=10, padx=10, fill="both", expand=True)
        
        ctk.CTkLabel(visual_container, text="Cache Contents", 
                    font=("Arial", 14, "bold")).pack(anchor="w", pady=(5, 10))
        
        self.cache_frame = ctk.CTkFrame(visual_container, bg_color=self.dark_bg)
        self.cache_frame.pack(pady=10, fill="both", expand=True)

    def toggle_hex_mode(self):
        if self.hex_mode.get():
            self.input_mode_label.configure(text="HEX", fg_color="#4b1d3f")
        else:
            self.input_mode_label.configure(text="DEC", fg_color="#3b3b3b")
        
        self.addr_entry.delete(0, "end")
        self.create_new_cache()

    def on_type_change(self, choice=None):
        if choice == "Set Associative" or self.cache_type.get() == "Set Associative":
            self.set_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
            self.set_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        else:
            self.set_label.grid_forget()
            self.set_entry.grid_forget()
        self.create_new_cache()

    def on_config_change(self, *args):
        self.create_new_cache()

    def create_new_cache(self):
        self.active_cache = Cache(
            size=self.validate_int(self.cache_size.get(), 4),
            policy=self.policy.get(),
            cache_type=self.cache_type.get(),
            set_count=self.validate_int(self.set_count.get(), 2)
        )
        
        self.addresses = []
        self.addr_display.configure(state="normal")
        self.addr_display.delete("1.0", "end")
        self.addr_display.insert("end", "Address Sequence:\n")
        self.addr_display.configure(state="disabled")
    
        self.stats_label.configure(text="Hits: 0  Misses: 0  Hit Ratio: 0.00")
        self.update_visualization()

    def add_address(self):
        val = self.addr_entry.get().strip()
        
        try:
            if self.hex_mode.get():
                if val.startswith("0x"):
                    val = val[2:]
                
                int_val = int(val, 16)
                display_val = f"0x{val}"
            else:
                if not val.isdigit():
                    raise ValueError("Not a valid decimal number")
                int_val = int(val)
                display_val = val
                
            self.addresses.append(int_val)
            self.addr_entry.delete(0, "end")
            
            self.addr_display.configure(state="normal")
            self.addr_display.insert("end", f"{display_val} ")
            self.addr_display.configure(state="disabled")            
            
            if self.active_cache:
                self.active_cache.access(int_val)
                hits, misses, ratio = self.active_cache.get_stats()
                self.stats_label.configure(text=f"Hits: {hits}  Misses: {misses}  Hit Ratio: {ratio:.2f}")
                self.update_visualization()
                
        except ValueError:
            current_mode = "hexadecimal" if self.hex_mode.get() else "decimal"
            error_msg = f"Invalid {current_mode} input"
            
            error_window = ctk.CTkToplevel(self)
            error_window.title("Input Error")
            error_window.geometry("300x100")
            error_window.resizable(False, False)
            
            ctk.CTkLabel(error_window, text=error_msg, font=("Arial", 14)).pack(pady=20)
            ctk.CTkButton(error_window, text="OK", command=error_window.destroy).pack()

    def update_visualization(self):
        for widget in self.cache_frame.winfo_children():
            widget.destroy()

        if not self.active_cache:
            return

        visual = self.active_cache.get_visual()
        
        value_formatter = lambda v: f"0x{v:X}" if v is not None and self.hex_mode.get() else str(v)
        
        if self.cache_type.get() == "Fully Associative":
            header_text = "Fully Associative Cache"
            if self.policy.get() == "FIFO":
                header_text += " (Position Based: New entries replace oldest ones)"
            else:
                header_text += " (LRU: Each hit updates usage tracking without moving blocks)"
            ctk.CTkLabel(self.cache_frame, text=header_text).pack(pady=(0, 5))
            
        elif self.cache_type.get() == "Direct Mapped":
            ctk.CTkLabel(self.cache_frame, text="Direct Mapped Cache (Index: Value)").pack(pady=(0, 5))
            
        elif self.cache_type.get() == "Set Associative":
            header_text = "Set Associative Cache"
            if self.policy.get() == "FIFO":
                header_text += " (Position Based within sets)"
            else:
                header_text += " (LRU within sets, tracking without moving blocks)"
            ctk.CTkLabel(self.cache_frame, text=header_text).pack(pady=(0, 5))
        
        if self.cache_type.get() == "Set Associative":
            for set_name, blocks in visual:
                set_frame = ctk.CTkFrame(self.cache_frame, bg_color=self.dark_bg)
                set_frame.pack(pady=3, fill="x")
                
                ctk.CTkLabel(set_frame, text=f"{set_name}:", text_color="skyblue").pack(side="left", padx=(0, 5))
                
                for i, b in enumerate(blocks):
                    block_frame = ctk.CTkFrame(set_frame, fg_color="gray25", corner_radius=5, bg_color=self.dark_bg)
                    block_frame.pack(side="left", padx=2)
                    
                    position_label = f"Pos {i}"
                    ctk.CTkLabel(block_frame, text=position_label, font=("Arial", 10), 
                                text_color="lightblue").pack(pady=(2, 0))
                    
                    val_text = value_formatter(b) if b is not None else "-"
                    ctk.CTkLabel(block_frame, text=val_text, width=50).pack(pady=(0, 2))
        else:
            row = ctk.CTkFrame(self.cache_frame, bg_color=self.dark_bg)
            row.pack()
            
            if self.cache_type.get() == "Direct Mapped":
                
                for idx, val in enumerate(visual):
                    block_frame = ctk.CTkFrame(row, fg_color="gray25", corner_radius=5, bg_color=self.dark_bg)
                    block_frame.pack(side="left", padx=2)
                    
                    ctk.CTkLabel(block_frame, text=f"Idx {idx}", font=("Arial", 10), 
                                text_color="lightblue").pack(pady=(2, 0))
                    
                    val_text = value_formatter(val) if val is not None else "-"
                    ctk.CTkLabel(block_frame, text=val_text, width=50).pack(pady=(0, 2))
            else:
                for i, b in enumerate(visual):
                    block_frame = ctk.CTkFrame(row, fg_color="gray25", corner_radius=5, bg_color=self.dark_bg)
                    block_frame.pack(side="left", padx=2)
                    
                    position_label = f"Pos {i}"
                    ctk.CTkLabel(block_frame, text=position_label, font=("Arial", 10), 
                                text_color="lightblue").pack(pady=(2, 0))
                    
                    val_text = value_formatter(b) if b is not None else "-"
                    ctk.CTkLabel(block_frame, text=val_text, width=50).pack(pady=(0, 2))

if __name__ == "__main__":
    app = App()
    app.mainloop()
