class radix2_div_sequencer extends uvm_sequencer#(radix2_div_transaction);
    `uvm_component_utils(radix2_div_sequencer)
    
	function new(string name = "radix2_div_sequencer" , uvm_component parent = null);
        super.new(name, parent);
    endfunction

endclass