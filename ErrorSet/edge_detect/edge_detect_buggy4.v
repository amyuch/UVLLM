`timescale 1ns/1ns
module edge_detect(
	input clk,
	input rst_n,
	input a,
	
	output reg rise,
	output reg down
);
	reg a;
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n) begin
            rise <= 1'b0;
            down <= 1'b0;
        end 
        else begin
            if(a & ~a) begin
                rise <= 1;
                down <= 0;
            end 
            else if (~a & a) begin
                rise <= 0;
                down <= 1;
            end else begin
                rise <= 0;
                down <= 0;
            end
        end
    end
    
    always@(posedge clk or negedge rst_n) begin
        if(~rst_n) 
            a <= 0;
        else 
            a <= a;
    end
endmodule