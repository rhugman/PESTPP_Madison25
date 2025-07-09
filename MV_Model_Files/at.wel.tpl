ptf ~ 
begin options
  PRINT_INPUT
  PRINT_FLOWS
  SAVE_FLOWS
end options

begin dimensions
  MAXBOUND 3
end dimensions

begin period 1
 5  6 15  ~   wflux_k:4_i:5_j:14  ~
 5 35 16  ~   wflux_k:4_i:34_j:15  ~
 5 33  6  ~   wflux_k:4_i:32_j:5  ~
end period
