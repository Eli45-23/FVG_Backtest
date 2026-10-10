import {expect,test,vi,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import SimpleSearchReport from '../src/SimpleSearchReport';
import {api} from '../src/api';
vi.mock('../src/api',()=>({api:vi.fn()}));afterEach(()=>{cleanup();vi.clearAllMocks()});
test('offers verified study',async()=>{vi.mocked(api).mockResolvedValue({ready:true,events:18931});render(<SimpleSearchReport/>);expect(await screen.findByText(/18,931 raw signals/)).toBeInTheDocument();expect(screen.getByRole('link')).toHaveAttribute('href','/api/research/simple-search/view')});
test('does not offer unverified study',async()=>{vi.mocked(api).mockResolvedValue({ready:false});render(<SimpleSearchReport/>);expect(await screen.findByText('Verification pending.')).toBeInTheDocument();expect(screen.queryByRole('link')).not.toBeInTheDocument()});
